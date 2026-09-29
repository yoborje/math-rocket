// Keeps Math Rocket working with no internet once it has been opened one time.
// build.sh stamps a new version below whenever the game or voice changes, so tablets pick up updates.
var CACHE = "math-rocket-53c8040399";
var FILES = ["./", "index.html", "manifest.webmanifest", "voice.mp4", "voice.json",
             "icon-192.png", "icon-512.png", "apple-touch-icon.png"];

self.addEventListener("install", function(e){
  e.waitUntil(caches.open(CACHE).then(function(c){ return c.addAll(FILES); }).then(function(){ return self.skipWaiting(); }));
});

self.addEventListener("activate", function(e){
  e.waitUntil(caches.keys().then(function(keys){
    return Promise.all(keys.filter(function(k){ return k !== CACHE; }).map(function(k){ return caches.delete(k); }));
  }).then(function(){ return self.clients.claim(); }));
});

// Cache first, then the network. Anything else fetched (like the rounded font) is saved for next time.
self.addEventListener("fetch", function(e){
  if (e.request.method !== "GET") return;
  e.respondWith(caches.match(e.request, {ignoreSearch: true}).then(function(hit){
    if (hit) return hit;
    return fetch(e.request).then(function(res){
      if (res && (res.ok || res.type === "opaque")){
        var copy = res.clone();
        caches.open(CACHE).then(function(c){ c.put(e.request, copy); });
      }
      return res;
    }).catch(function(){
      if (e.request.mode === "navigate") return caches.match("index.html");
    });
  }));
});
