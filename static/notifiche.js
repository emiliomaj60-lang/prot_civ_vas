async function attivaNotifiche() {
    console.log("Attivazione notifiche...");

    const registration = await navigator.serviceWorker.register('/service-worker.js');
    console.log("Service worker registrato:", registration);

    const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: vapidPublicKey
    });

    console.log("Subscription creata:", subscription);

    await fetch("/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            endpoint: subscription.endpoint,
            keys: {
                p256dh: btoa(String.fromCharCode.apply(null, new Uint8Array(subscription.getKey("p256dh")))),
                auth: btoa(String.fromCharCode.apply(null, new Uint8Array(subscription.getKey("auth"))))
            },
            telefono: telefonoUtente,
            gruppo: categoriaUtente
        })
    });

    console.log("Subscription inviata al server");
    alert("Notifiche attivate");
}