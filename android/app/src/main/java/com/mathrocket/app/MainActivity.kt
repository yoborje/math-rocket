package com.mathrocket.app

import android.annotation.SuppressLint
import android.app.Activity
import android.graphics.Color
import android.os.Build
import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.view.View
import android.view.WindowInsets
import android.view.WindowInsetsController
import android.webkit.JavascriptInterface
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.webkit.WebViewAssetLoader
import java.util.Locale

/**
 * Hosts the game (assets/index.html) in a full-screen WebView.
 * Everything is bundled in the APK, so the app works with no internet.
 */
class MainActivity : Activity() {

    private lateinit var web: WebView
    private var tts: TextToSpeech? = null
    private var ttsReady = false

    // Serves assets from a real https origin so localStorage (saved stars) works reliably.
    private val assetLoader by lazy {
        WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        web = WebView(this).apply {
            setBackgroundColor(Color.parseColor("#150F3B"))
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.mediaPlaybackRequiresUserGesture = false
            settings.allowFileAccess = false
            settings.allowContentAccess = false
            settings.textZoom = 100
            webViewClient = object : WebViewClient() {
                override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest): WebResourceResponse? =
                    assetLoader.shouldInterceptRequest(request.url)

                // Keep kids inside the game: never navigate anywhere else.
                override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean =
                    request.url.host != WebViewAssetLoader.DEFAULT_DOMAIN
            }
            addJavascriptInterface(SpeechBridge(), "AndroidTTS")
        }
        setContentView(web)

        tts = TextToSpeech(this) { status ->
            if (status == TextToSpeech.SUCCESS) {
                tts?.let { t ->
                    t.language = Locale.UK
                    pickTeacherVoice(t)
                    t.setPitch(1.0f)
                    t.setSpeechRate(0.92f)
                }
                ttsReady = true
            }
        }

        if (savedInstanceState != null) {
            web.restoreState(savedInstanceState)
        } else {
            web.loadUrl("https://${WebViewAssetLoader.DEFAULT_DOMAIN}/assets/index.html")
        }
    }

    // Chooses a natural-sounding British woman's voice that works offline.
    // Google's offline UK voices "gba", "gbc" and "gbg" are female ("gbd" and "rjs" are male);
    // Samsung names female voices "...SMTf..". Falls back to any female English voice.
    private fun pickTeacherVoice(t: TextToSpeech) {
        val voices = try { t.voices } catch (e: Exception) { null } ?: return
        val femaleIds = listOf("gba", "gbc", "gbg", "smtf", "female", "sfg", "tpf", "iob", "iog")
        val maleIds = listOf("gbd", "rjs", "smtm", "#male", "iol", "iom", "tpd")
        val best = voices
            .filter { v ->
                val n = v.name.lowercase(Locale.ROOT)
                v.locale.language == "en" &&
                    !v.isNetworkConnectionRequired &&
                    v.features?.contains(TextToSpeech.Engine.KEY_FEATURE_NOT_INSTALLED) != true &&
                    maleIds.none { n.contains(it) }
            }
            .maxByOrNull { v ->
                val n = v.name.lowercase(Locale.ROOT)
                var score = v.quality
                if (v.locale.country == "GB") score += 600
                val rank = femaleIds.indexOfFirst { n.contains(it) }
                if (rank >= 0) score += 400 - rank * 10
                score
            }
        if (best != null) t.voice = best
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus) hideSystemBars()
    }

    private fun hideSystemBars() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            window.insetsController?.let {
                it.hide(WindowInsets.Type.systemBars())
                it.systemBarsBehavior = WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
            }
        } else {
            @Suppress("DEPRECATION")
            window.decorView.systemUiVisibility = (View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                or View.SYSTEM_UI_FLAG_FULLSCREEN
                or View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                or View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                or View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                or View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN)
        }
    }

    // The game handles Back itself (close popup, leave level, and so on) and
    // returns false on the home screen, which closes the app.
    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        web.evaluateJavascript("window.mrBack ? window.mrBack() : false") { handled ->
            if (handled != "true") {
                @Suppress("DEPRECATION")
                super.onBackPressed()
            }
        }
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        web.saveState(outState)
    }

    override fun onPause() {
        super.onPause()
        tts?.stop()
        web.onPause()
    }

    override fun onResume() {
        super.onResume()
        web.onResume()
    }

    override fun onDestroy() {
        tts?.shutdown()
        web.destroy()
        super.onDestroy()
    }

    /** Called from the game as window.AndroidTTS.speakStyled("What is 3 add 4?", 1.0, 0.92) */
    inner class SpeechBridge {
        @JavascriptInterface
        fun speak(text: String) = speakStyled(text, 1.0, 0.92)

        @JavascriptInterface
        fun speakStyled(text: String, pitch: Double, rate: Double) {
            val t = tts ?: return
            if (!ttsReady) return
            t.setPitch(pitch.toFloat())
            t.setSpeechRate(rate.toFloat())
            t.speak(text, TextToSpeech.QUEUE_FLUSH, null, "mathrocket")
        }
    }
}
