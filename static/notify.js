(function () {
    const countEl = document.getElementById("bloomBellCount");
    const listEl = document.getElementById("bloomBellList");
    const bell = document.getElementById("bloomBell");
    if (!countEl || !listEl || !bell) return;

    function render(data) {
        const unread = data.unread || 0;
        countEl.textContent = unread;
        countEl.classList.toggle("hidden", unread < 1);
        const items = data.items || [];
        if (!items.length) {
            listEl.innerHTML = '<p class="text-xs text-[#4A5D23]/70">No updates yet.</p>';
            return;
        }
        listEl.innerHTML = items
            .map(function (item) {
                const body = (item.message || "").replace(/</g, "&lt;").slice(0, 280);
                const href = item.href || "/";
                return (
                    '<a href="' +
                    href +
                    '" class="block text-xs mb-2 pb-2 border-b border-[#4A5D23]/10">' +
                    '<span class="font-bold uppercase text-[#E3256B]">' +
                    (item.kind || "info") +
                    "</span>" +
                    '<p class="whitespace-pre-wrap mt-1">' +
                    body +
                    "</p></a>"
                );
            })
            .join("");
    }

    function poll() {
        fetch("/api/notifications", { credentials: "same-origin" })
            .then(function (res) {
                return res.ok ? res.json() : null;
            })
            .then(function (data) {
                if (data) render(data);
            })
            .catch(function () {});
    }

    bell.addEventListener("click", function (event) {
        event.preventDefault();
        listEl.classList.toggle("hidden");
        if (!listEl.classList.contains("hidden")) {
            fetch("/api/notifications/read", { method: "POST", credentials: "same-origin" });
            countEl.classList.add("hidden");
        }
    });

    document.addEventListener("click", function (event) {
        const wrap = document.getElementById("bloomBellWrap");
        if (wrap && !wrap.contains(event.target)) {
            listEl.classList.add("hidden");
        }
    });

    poll();
    setInterval(poll, 20000);
})();
