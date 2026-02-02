self.addEventListener("push", event => {
    let data = {};

    try {
        data = event.data ? event.data.json() : {};
    } catch (e) {
        console.error("Errore parsing push:", e);
    }

    const title = data.title || "Notifica Protezione Civile";
    const body  = data.body  || "Hai un nuovo messaggio di emergenza.";

    event.waitUntil(
        self.registration.showNotification(title, {
            body: body,
            icon: "/static/icon.png"
        })
    );
});