(() => {
    "use strict";

    const app = document.getElementById("education-app");
    if (!app) return;

    const isAuthenticated = app.dataset.authenticated === "true";
    const isOwner = app.dataset.owner === "true";
    const csrfToken = app.querySelector('[name="csrfmiddlewaretoken"]').value;
    const searchForm = document.getElementById("education-search-form");
    const searchInput = document.getElementById("education-search");
    const grid = document.getElementById("education-grid");
    const resultCount = document.getElementById("education-results");
    const states = {
        loading: document.getElementById("education-loading"),
        error: document.getElementById("education-error"),
        empty: document.getElementById("education-empty"),
        grid,
    };
    const addDialog = document.getElementById("education-add-dialog");
    const educationForm = document.getElementById("education-form");
    const deleteDialog = document.getElementById("education-delete-dialog");
    const deleteForm = document.getElementById("education-delete-form");
    const items = new Map();
    const pendingStars = new Set();
    const SEARCH_DEBOUNCE_DELAY = 300;
    let searchTimer;
    let listController;
    let dataRevision = 0;
    let selectedForDeletion = null;

    function setState(activeState, message = "") {
        for (const [name, node] of Object.entries(states)) {
            node.hidden = name !== activeState;
        }
        app.setAttribute("aria-busy", String(activeState === "loading"));
        resultCount.hidden = activeState !== "grid";

        if (activeState === "error") {
            document.getElementById("education-error-message").textContent = message;
        }
        if (activeState === "empty") {
            document.getElementById("education-empty-message").textContent = message;
        }
    }

    async function requestJson(url, options = {}) {
        let response;
        try {
            response = await fetch(url, {
                credentials: "same-origin",
                ...options,
                headers: { Accept: "application/json", ...options.headers },
            });
        } catch (error) {
            if (error.name === "AbortError") throw error;
            throw new Error("Tidak dapat terhubung ke server. Coba lagi.");
        }

        let data;
        try {
            data = await response.json();
        } catch (error) {
            if (error.name === "AbortError") throw error;
            throw new Error(response.status === 403
                ? "Permintaan ditolak. Muat ulang halaman lalu coba lagi."
                : `Respons server tidak valid (HTTP ${response.status}).`);
        }

        if (!response.ok) {
            const messages = Object.values(data.errors || {})
                .flat()
                .map(error => error.message)
                .filter(Boolean);
            const error = new Error(messages.join(" ")
                || data.message
                || `Permintaan gagal (HTTP ${response.status}).`);
            error.fields = data.errors || {};
            throw error;
        }
        return data;
    }

    function postJson(url, body) {
        return requestJson(url, {
            method: "POST",
            headers: { "X-CSRFToken": csrfToken },
            body,
        });
    }

    function makeElement(tag, className, text) {
        const node = document.createElement(tag);
        node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    }

    function updateStarButton(button, fields) {
        button.classList.toggle("is-starred", fields.is_starred);
        button.setAttribute("aria-pressed", String(fields.is_starred));
        const label = fields.is_starred ? "Batalkan star" : "Beri star";
        button.textContent = `★ ${label} (${fields.star_count})`;
    }

    function buildCard(item) {
        const fields = item.fields;
        const article = makeElement("article", "education-card");
        article.append(
            makeElement("h2", "", fields.title),
            makeElement("p", "education-description", fields.description),
            makeElement("p", "education-start_year-end_year",
                `${fields.start_year} — ${fields.end_year}`)
        );

        const actions = makeElement("div", "education-actions");
        if (isAuthenticated) {
            const button = makeElement("button", "button button-star");
            button.type = "button";
            button.dataset.action = "star";
            button.dataset.id = item.pk;
            button.disabled = pendingStars.has(item.pk);
            updateStarButton(button, fields);
            actions.append(button);
        } else {
            const link = makeElement("a", "button button-star",
                `★ Login untuk memberi star (${fields.star_count})`);
            link.href = app.dataset.loginUrl;
            actions.append(link);
        }

        if (isOwner) {
            const button = makeElement("button", "button button-danger", "Hapus");
            button.type = "button";
            button.dataset.action = "delete";
            button.dataset.id = item.pk;
            actions.append(button);
        }
        article.append(actions);
        return article;
    }

    function renderItems(data) {
        items.clear();
        const fragment = document.createDocumentFragment();
        for (const item of data) {
            items.set(item.pk, item);
            fragment.append(buildCard(item));
        }
        grid.replaceChildren(fragment);
        resultCount.textContent = `${data.length} pendidikan ditemukan.`;
    }

    async function loadEducation() {
        clearTimeout(searchTimer);
        listController?.abort();
        const controller = new AbortController();
        listController = controller;
        const revision = dataRevision;
        const query = searchInput.value.trim();
        const url = new URL(app.dataset.listUrl, window.location.origin);
        if (query) url.searchParams.set("title", query);
        setState("loading");

        try {
            const data = await requestJson(url, { signal: controller.signal });
            if (controller.signal.aborted) return;
            // Pencarian yang dimulai sebelum perubahan star harus membaca ulang data.
            if (revision !== dataRevision) return loadEducation();
            if (!Array.isArray(data)) throw new Error("Format daftar pendidikan tidak valid.");
            renderItems(data);
            if (data.length) {
                setState("grid");
            } else {
                setState("empty", query
                    ? "Tidak ada pendidikan yang sesuai dengan pencarian."
                    : "Belum ada edukasi yang ditambahkan.");
            }
        } catch (error) {
            if (controller.signal.aborted || error.name === "AbortError") return;
            setState("error", error.message);
        }
    }

    function setFormBusy(form, busy) {
        form.dataset.busy = String(busy);
        form.querySelectorAll("button").forEach(button => {
            button.disabled = busy;
        });
    }

    function showFormErrors(errors = {}) {
        let firstInvalidField = null;
        educationForm.querySelectorAll("[data-error-for]").forEach(node => {
            const name = node.dataset.errorFor;
            const field = educationForm.elements.namedItem(name);
            const messages = errors[name] || [];
            node.textContent = messages.map(error => error.message).join(" ");
            node.hidden = messages.length === 0;
            field.setAttribute("aria-describedby", node.id);
            if (messages.length) {
                field.setAttribute("aria-invalid", "true");
                firstInvalidField ||= field;
            } else {
                field.removeAttribute("aria-invalid");
            }
        });
        firstInvalidField?.focus();
    }

    function findStarButton(id) {
        return grid.querySelector(`[data-action="star"][data-id="${id}"]`);
    }

    async function toggleStar(item, button) {
        if (pendingStars.has(item.pk)) return;
        pendingStars.add(item.pk);
        button.disabled = true;
        try {
            const result = await postJson(item.urls.star);
            dataRevision += 1;
            const currentItem = items.get(item.pk);
            const currentButton = findStarButton(item.pk);
            if (currentItem && currentButton) {
                currentItem.fields.star_count = result.star_count;
                currentItem.fields.is_starred = result.is_starred;
                updateStarButton(currentButton, currentItem.fields);
            }
            showToast("Berhasil", result.message, "success");
        } catch (error) {
            showToast("Gagal memperbarui star", error.message, "error");
        } finally {
            pendingStars.delete(item.pk);
            const currentButton = findStarButton(item.pk);
            if (currentButton) currentButton.disabled = false;
        }
    }

    grid.addEventListener("click", event => {
        const button = event.target.closest("button[data-action]");
        if (!button || !grid.contains(button)) return;
        const item = items.get(button.dataset.id);
        if (!item) return;
        if (button.dataset.action === "star") toggleStar(item, button);
        if (button.dataset.action === "delete" && deleteDialog) {
            selectedForDeletion = item;
            document.getElementById("education-delete-name").textContent = item.fields.title;
            deleteDialog.showModal();
        }
    });

    searchInput.addEventListener("input", () => {
        clearTimeout(searchTimer);
        listController?.abort();
        searchTimer = setTimeout(loadEducation, SEARCH_DEBOUNCE_DELAY);
    });
    searchForm.addEventListener("submit", event => {
        event.preventDefault();
        loadEducation();
    });
    document.getElementById("education-retry").addEventListener("click", loadEducation);

    app.querySelectorAll("[data-close-dialog]").forEach(button => {
        button.addEventListener("click", () => button.closest("dialog").close());
    });
    app.querySelectorAll("dialog").forEach(dialog => {
        dialog.addEventListener("cancel", event => {
            if (dialog.querySelector("form")?.dataset.busy === "true") event.preventDefault();
        });
    });

    if (educationForm && addDialog) {
        document.getElementById("open-education-modal").addEventListener("click", () => {
            showFormErrors();
            addDialog.showModal();
        });
        educationForm.addEventListener("submit", async event => {
            event.preventDefault();
            if (educationForm.dataset.busy === "true") return;
            showFormErrors();
            const formData = new FormData(educationForm);
            setFormBusy(educationForm, true);
            try {
                const result = await postJson(app.dataset.createUrl, formData);
                dataRevision += 1;
                educationForm.reset();
                addDialog.close();
                showToast("Berhasil", result.message, "success");
                await loadEducation();
            } catch (error) {
                showFormErrors(error.fields || {});
                showToast("Gagal menambah pendidikan", error.message, "error");
            } finally {
                setFormBusy(educationForm, false);
            }
        });
    }

    if (deleteForm && deleteDialog) {
        deleteForm.addEventListener("submit", async event => {
            event.preventDefault();
            if (!selectedForDeletion || deleteForm.dataset.busy === "true") return;
            const item = selectedForDeletion;
            setFormBusy(deleteForm, true);
            try {
                const result = await postJson(item.urls.delete);
                dataRevision += 1;
                deleteDialog.close();
                selectedForDeletion = null;
                showToast("Berhasil", result.message, "success");
                await loadEducation();
                searchInput.focus();
            } catch (error) {
                showToast("Gagal menghapus pendidikan", error.message, "error");
            } finally {
                setFormBusy(deleteForm, false);
            }
        });
    }

    loadEducation();
})();
