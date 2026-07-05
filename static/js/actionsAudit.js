console.log("actionsAudit.js loaded");

document.addEventListener("DOMContentLoaded", getactionsAudit);

document.addEventListener("DOMContentLoaded", () => {
  const logoutLink = document.getElementById("logoutLink");

  if (logoutLink) {
    logoutLink.addEventListener("click", function (e) {
      const confirmed = confirm("Are you sure you want to log out?");
      if (!confirmed) {
        e.preventDefault(); // Cancel the logout
      }
    });
  }
});

document.addEventListener("DOMContentLoaded", () => {
  const adminLink = document.getElementById("adminLink");

  if (adminLink) {
    adminLink.addEventListener("click", function (e) {
      const confirmed = confirm(
        "Are you sure you want to leave the application?",
      );
      if (!confirmed) {
        e.preventDefault();
      }
    });
  }
});

document.addEventListener("DOMContentLoaded", () => {
  const userLink = document.getElementById("userLink");

  if (userLink) {
    userLink.addEventListener("click", function (e) {
      const confirmed = confirm(
        "Are you sure you want to leave the application?",
      );
      if (!confirmed) {
        e.preventDefault();
      }
    });
  }
});

// Fetch and display all actions audit
function getactionsAudit() {
  fetch("/api/actionsAudit")
    .then((res) => res.json())
    .then((data) => {
      const tableBody = document.querySelector("#actionsAuditTable tbody");
      tableBody.innerHTML = "";
      data.forEach((action) => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${action.id}</td>
          <td>${action.action}</td>
          <td>${action.user}</td>
          <td>${action.timestamp}</td>
        `;
        tableBody.appendChild(row);
      });
    })
    .catch((error) => {
      showMessage("Error fetching actions audit", "red");
      console.error("Fetch error:", error);
    });
}

// Message display
function showMessage(text, color) {
  let msgDiv = document.getElementById("message");
  if (!msgDiv) {
    msgDiv = document.createElement("div");
    msgDiv.id = "message";
    document.body.prepend(msgDiv);
  }

  msgDiv.textContent = text;
  msgDiv.style.color = color;
  msgDiv.style.fontWeight = "bold";

  setTimeout(() => {
    msgDiv.textContent = "";
  }, 3000);
}
