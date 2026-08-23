// =========================================
// Theme Management (Dark / Light Mode)
// =========================================

function getSavedTheme() {
    return localStorage.getItem("theme") || "dark";
}

function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
    
    // Update theme toggle button text & icon state
    const themeTextEl = document.querySelector(".theme-text");
    if (themeTextEl) {
        themeTextEl.textContent = theme === "dark" ? "Light Mode" : "Dark Mode";
    }

    // Update Chart.js if active
    if (window.myClassificationChart) {
        const isDark = theme === "dark";
        const legendColor = isDark ? "#94a3b8" : "#475569";
        const borderColor = isDark ? "#0b0f19" : "#ffffff";
        
        window.myClassificationChart.options.plugins.legend.labels.color = legendColor;
        window.myClassificationChart.data.datasets[0].borderColor = borderColor;
        window.myClassificationChart.update('active');
    }
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
    const nextTheme = currentTheme === "dark" ? "light" : "dark";
    applyTheme(nextTheme);
}

// Initialize theme immediately on script load to prevent flash
(function() {
    const savedTheme = getSavedTheme();
    document.documentElement.setAttribute("data-theme", savedTheme);
})();

document.addEventListener("DOMContentLoaded", function() {
    const themeTextEl = document.querySelector(".theme-text");
    if (themeTextEl) {
        const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
        themeTextEl.textContent = currentTheme === "dark" ? "Light Mode" : "Dark Mode";
    }
});


// =========================================
// Email Filtering and Searching
// =========================================

function filterAndSearch() {
    let searchInput = document.getElementById("searchInput");
    let searchText = searchInput ? searchInput.value.toLowerCase().trim() : "";
    let activeFilter = window.currentFilter || "all";
    let emails = document.getElementsByClassName("email-card-glass");

    if (emails.length === 0) {
        emails = document.getElementsByClassName("email-card");
    }

    let visibleCount = 0;

    for (let i = 0; i < emails.length; i++) {
        let email = emails[i];
        let searchData = email.getAttribute("data-search") || "";
        let classification = email.getAttribute("data-classification") || "";

        searchData = searchData.toLowerCase();
        let matchesSearch = !searchText || searchData.includes(searchText);
        let matchesFilter = activeFilter === "all" || classification === activeFilter;

        if (matchesSearch && matchesFilter) {
            if (email.style.display === "none") {
                email.style.display = "flex";
                email.style.opacity = "0";
                email.style.transform = "translateY(10px)";
                requestAnimationFrame(() => {
                    email.style.transition = "opacity 0.3s cubic-bezier(0.16, 1, 0.3, 1), transform 0.3s cubic-bezier(0.16, 1, 0.3, 1)";
                    email.style.opacity = "1";
                    email.style.transform = "translateY(0)";
                });
            } else {
                email.style.display = "flex";
            }
            visibleCount++;
        } else {
            email.style.display = "none";
        }
    }

    let emailCount = document.getElementById("emailCount");
    if (emailCount) {
        emailCount.innerText = "Showing " + visibleCount + " email" + (visibleCount === 1 ? "" : "s");
    }
}

function searchEmails() {
    filterAndSearch();
}

function filterEmails(type, btnElement) {
    window.currentFilter = type;

    let buttons = document.querySelectorAll(".filter-btn");
    buttons.forEach(btn => btn.classList.remove("active"));

    if (btnElement) {
        btnElement.classList.add("active");
    }

    filterAndSearch();
}


// =========================================
// Manual Classification Override Action
// =========================================

function markEmail(emailId, newLabel, btnElement) {
    if (!emailId || !newLabel) return;

    if (btnElement) {
        btnElement.disabled = true;
    }

    fetch("/api/mark_email", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            email_id: emailId,
            label: newLabel
        })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            alert(data.error || "Failed to update email classification.");
            if (btnElement) btnElement.disabled = false;
            return;
        }

        const isSpam = newLabel === "spam";

        // Update elements with matching data-email-id
        const targets = document.querySelectorAll(`[data-email-id="${emailId}"]`);
        targets.forEach(target => {
            target.setAttribute("data-classification", newLabel);

            // Update status badge
            const badge = target.querySelector(".badge-status");
            if (badge) {
                const isLg = badge.classList.contains("badge-lg");
                badge.className = `badge-status ${isSpam ? "badge-spam" : "badge-safe"} ${isLg ? "badge-lg" : ""}`;
                badge.innerHTML = isSpam
                    ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg><span>${isLg ? "CLASSIFIED AS SPAM" : "SPAM"}</span>`
                    : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg><span>${isLg ? "VERIFIED SAFE" : "SAFE"}</span>`;
                
                // Pop animation effect
                badge.style.transform = "scale(1.2)";
                setTimeout(() => {
                    badge.style.transform = "scale(1)";
                }, 200);
            }

            // Update action button
            const actionContainer = target.querySelector(".override-actions") || target.querySelector(".detail-actions");
            if (actionContainer) {
                actionContainer.innerHTML = isSpam
                    ? `<button type="button" class="btn-action btn-mark-safe" onclick="markEmail('${emailId}', 'ham', this)" title="Mark as Safe email"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg><span>Mark Safe</span></button>`
                    : `<button type="button" class="btn-action btn-mark-spam" onclick="markEmail('${emailId}', 'spam', this)" title="Mark as Spam"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg><span>Mark Spam</span></button>`;
            }

            // Ensure custom override pill is present
            let overrideBadge = target.querySelector(".custom-override-pill");
            if (!overrideBadge) {
                const headerGroup = target.querySelector(".email-sender-address") || target.querySelector(".detail-meta");
                if (headerGroup) {
                    const tag = document.createElement("span");
                    tag.className = "custom-override-pill";
                    tag.innerHTML = "⚡ User Override";
                    headerGroup.appendChild(tag);
                }
            }
        });

        // Update statistics cards
        if (data.stats) {
            const spamNum = document.querySelector(".stat-rose .stat-number");
            const safeNum = document.querySelector(".stat-emerald .stat-number");
            const percNum = document.querySelector(".stat-purple .stat-number");
            const fillBar = document.querySelector(".stat-progress-fill");

            if (spamNum) spamNum.textContent = data.stats.spam_emails;
            if (safeNum) safeNum.textContent = data.stats.safe_emails;
            if (percNum) percNum.textContent = data.stats.spam_percentage + "%";
            if (fillBar) fillBar.style.setProperty("--progress-width", data.stats.spam_percentage + "%");

            // Update Chart.js dataset
            if (window.myClassificationChart) {
                window.myClassificationChart.data.datasets[0].data = [data.stats.spam_emails, data.stats.safe_emails];
                window.myClassificationChart.update('active');
            }
        }

        // Re-filter list visibility based on active tab
        filterAndSearch();
    })
    .catch(err => {
        console.error("Error marking email:", err);
        alert("Failed to connect to server.");
        if (btnElement) btnElement.disabled = false;
    });
}


// =========================================
// Checkbox Selection & Trash Operations
// =========================================

function updateSelectionState() {
    const checkboxes = document.querySelectorAll(".email-card-glass:not([style*='display: none']) .email-checkbox");
    let checkedCount = 0;

    checkboxes.forEach(cb => {
        if (cb.checked) checkedCount++;
    });

    const btnDelete = document.getElementById("btnDeleteSelected");
    const countSpan = document.getElementById("selectedCount");
    const selectAllCb = document.getElementById("selectAllCheckbox");

    if (countSpan) {
        countSpan.textContent = checkedCount;
    }

    if (btnDelete) {
        btnDelete.style.display = checkedCount > 0 ? "inline-flex" : "none";
    }

    if (selectAllCb) {
        selectAllCb.checked = checkboxes.length > 0 && checkedCount === checkboxes.length;
    }
}

function toggleSelectAll(selectAllEl) {
    const isChecked = selectAllEl.checked;
    const visibleCards = document.querySelectorAll(".email-card-glass:not([style*='display: none'])");

    visibleCards.forEach(card => {
        const cb = card.querySelector(".email-checkbox");
        if (cb) {
            cb.checked = isChecked;
        }
    });

    updateSelectionState();
}

function deleteSelectedEmails() {
    const checkedBoxes = document.querySelectorAll(".email-checkbox:checked");
    const emailIds = Array.from(checkedBoxes).map(cb => cb.value);

    if (emailIds.length === 0) {
        alert("Please select at least one email to move to Trash.");
        return;
    }

    const confirmMsg = emailIds.length === 1 
        ? "Move 1 email to Gmail Trash?" 
        : `Move ${emailIds.length} emails to Gmail Trash?`;

    if (!confirm(confirmMsg)) return;

    const btnDelete = document.getElementById("btnDeleteSelected");
    if (btnDelete) {
        btnDelete.disabled = true;
        btnDelete.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin-icon"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg><span>Moving to Trash...</span>`;
    }

    fetch("/api/delete_emails", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            email_ids: emailIds
        })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            alert(data.error || "Failed to move emails to Gmail Trash.");
            if (btnDelete) {
                btnDelete.disabled = false;
                btnDelete.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg><span>Move to Trash (<span id="selectedCount">${emailIds.length}</span>)</span>`;
            }
            return;
        }

        // Animate removal of deleted email cards
        emailIds.forEach(id => {
            const card = document.querySelector(`.email-card-glass[data-email-id="${id}"]`);
            if (card) {
                card.style.transition = "all 0.3s cubic-bezier(0.16, 1, 0.3, 1)";
                card.style.opacity = "0";
                card.style.transform = "scale(0.95) translateY(-10px)";
                setTimeout(() => {
                    card.remove();
                    filterAndSearch();
                    updateSelectionState();
                }, 300);
            }
        });

        // Update statistics cards
        if (data.stats) {
            const totalNum = document.querySelector(".stat-indigo .stat-number");
            const spamNum = document.querySelector(".stat-rose .stat-number");
            const safeNum = document.querySelector(".stat-emerald .stat-number");
            const percNum = document.querySelector(".stat-purple .stat-number");
            const fillBar = document.querySelector(".stat-progress-fill");

            if (totalNum) totalNum.textContent = data.stats.total_emails;
            if (spamNum) spamNum.textContent = data.stats.spam_emails;
            if (safeNum) safeNum.textContent = data.stats.safe_emails;
            if (percNum) percNum.textContent = data.stats.spam_percentage + "%";
            if (fillBar) fillBar.style.setProperty("--progress-width", data.stats.spam_percentage + "%");

            if (window.myClassificationChart) {
                window.myClassificationChart.data.datasets[0].data = [data.stats.spam_emails, data.stats.safe_emails];
                window.myClassificationChart.update('active');
            }
        }
    })
    .catch(err => {
        console.error("Error moving emails to trash:", err);
        alert("Failed to connect to server.");
        if (btnDelete) btnDelete.disabled = false;
    });
}

function deleteSingleEmail(emailId, btnElement, isDetailsPage = false) {
    if (!emailId) return;

    if (!confirm("Move this email to Gmail Trash?")) return;

    if (btnElement) {
        btnElement.disabled = true;
    }

    fetch("/api/delete_emails", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            email_ids: [emailId]
        })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            alert(data.error || "Failed to move email to Gmail Trash.");
            if (btnElement) btnElement.disabled = false;
            return;
        }

        if (isDetailsPage) {
            window.location.href = "/dashboard";
            return;
        }

        const card = document.querySelector(`.email-card-glass[data-email-id="${emailId}"]`);
        if (card) {
            card.style.transition = "all 0.3s cubic-bezier(0.16, 1, 0.3, 1)";
            card.style.opacity = "0";
            card.style.transform = "scale(0.95) translateY(-10px)";
            setTimeout(() => {
                card.remove();
                filterAndSearch();
                updateSelectionState();
            }, 300);
        }

        if (data.stats) {
            const totalNum = document.querySelector(".stat-indigo .stat-number");
            const spamNum = document.querySelector(".stat-rose .stat-number");
            const safeNum = document.querySelector(".stat-emerald .stat-number");
            const percNum = document.querySelector(".stat-purple .stat-number");
            const fillBar = document.querySelector(".stat-progress-fill");

            if (totalNum) totalNum.textContent = data.stats.total_emails;
            if (spamNum) spamNum.textContent = data.stats.spam_emails;
            if (safeNum) safeNum.textContent = data.stats.safe_emails;
            if (percNum) percNum.textContent = data.stats.spam_percentage + "%";
            if (fillBar) fillBar.style.setProperty("--progress-width", data.stats.spam_percentage + "%");

            if (window.myClassificationChart) {
                window.myClassificationChart.data.datasets[0].data = [data.stats.spam_emails, data.stats.safe_emails];
                window.myClassificationChart.update('active');
            }
        }
    })
    .catch(err => {
        console.error("Error moving email to trash:", err);
        alert("Failed to connect to server.");
        if (btnElement) btnElement.disabled = false;
    });
}
