// Keeps Math Rocket working with no internet once it has been opened one time.
// build.sh stamps a new version below whenever the game or voice changes, so tablets pick up updates.
var CACHE = "math-rocket-__VERSION__";
var FILES = ["index.html", "manifest.webmanifest", "voice.mp4", "voice.json", "fonts/baloo2.woff2",
             "icon-192.png", "icon-512.png", "apple-touch-icon.png"];
// iPad Safari is strict about matching saved files, so match loosely.
var LOOSE = {ignoreSearch: true, ignoreVary: true};

self.addEventListener("install", function(e){
  e.waitUntil(caches.open(CACHE).then(function(c){
    // Fetch each file fresh (not from the browser's own cache) and save it.
    return Promise.all(FILES.map(function(f){
      return fetch(new Request(f, {cache: "reload"})).then(function(res){
        if (!res.ok) throw new Error(f + " " + res.status);
        return c.put(f, res);
      });
    }));
  }).then(function(){ return self.skipWaiting(); }));
});

self.addEventListener("activate", function(e){
  e.waitUntil(caches.keys().then(function(keys){
    return Promise.all(keys.filter(function(k){ return k !== CACHE; }).map(function(k){ return caches.delete(k); }));
  }).then(function(){ return self.clients.claim(); }));
});

self.addEventListener("fetch", function(e){
  var req = e.request;
  if (req.method !== "GET") return;

  // Opening the app, from any address inside it: always the saved game page.
  if (req.mode === "navigate"){
    e.respondWith(caches.open(CACHE).then(function(c){
      return c.match("index.html", LOOSE).then(function(page){ return page || fetch(req); });
    }));
    return;
  }

  e.respondWith(caches.open(CACHE).then(function(c){
    return c.match(req, LOOSE).then(function(hit){
      return hit || fetch(req).catch(function(){ return new Response("", {status: 504}); });
    });
  }));
});
