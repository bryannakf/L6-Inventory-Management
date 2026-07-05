console.log("inventory.js loaded");

// Load items on page load
document.addEventListener("DOMContentLoaded", getItems);

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
        "Are you sure you want to leave the application?"
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
        "Are you sure you want to leave the application?"
      );
      if (!confirmed) {
        e.preventDefault();
      }
    });
  }
});

// Fetch and display all items
function getItems() {
  fetch("/api/items")
    .then((res) => res.json())
    .then((data) => {
      const tableBody = document.querySelector("#itemTable tbody");
      tableBody.innerHTML = "";
      data.forEach((item) => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${item.id}</td>
          <td>${item.item_name}</td>
          <td>${item.quantity}</td>
          <td>${item.datacenter_id}</td>
        `;
        tableBody.appendChild(row);
      });
    })
    .catch((error) => {
      showMessage("Error fetching items", "red");
      console.error("Fetch error:", error);
    });
}

// Add item
document.getElementById("addItemForm").addEventListener("submit", function (e) {
  e.preventDefault();
  const item_name = document.getElementById("addItem_name").value;
  const quantity = document.getElementById("addQuantity").value;
  const datacenter_id = document.getElementById("addDatacenterID").value;

  fetch("/api/item", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ item_name, quantity, datacenter_id }),
  })
    .then((res) => res.json())
    .then((data) => {
      showMessage(data.message || "Item added", "green");
      getItems();
    })
    .catch((err) => {
      showMessage("Error adding item", "red");
      console.error("Add error:", err);
    });
});

// Update item
document
  .getElementById("updateItemForm")
  .addEventListener("submit", function (e) {
    e.preventDefault();
    const id = document.getElementById("updateItemID").value;
    const quantity = document.getElementById("updateQuantity").value;
    const datacenter_id = document.getElementById("updateDatacenterID").value;

    fetch(`/api/item/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ quantity, datacenter_id }),
    })
      .then((res) => {
        if (!res.ok) {
          return res.json().then((data) => {
            throw new Error(data.error || "Failed to update item");
          });
        }
        return res.json();
      })
      .then((data) => {
        showMessage(data.message || "Item updated", "green");
        getItems();
      })
      .catch((err) => {
        showMessage(err.message || "Error updating item", "red");
        console.error("Update error:", err);
      });
  });

// Delete item
document
  .getElementById("deleteItemForm")
  .addEventListener("submit", function (e) {
    e.preventDefault();
    const id = document.getElementById("deleteItemID").value;

    if (!id) {
      showMessage("Please enter a valid item ID", "red");
      return;
    }

    // prompt for confirmation
    const confirmed = confirm(
      `Are you sure you want to delete item with ID ${id}?`
    );
    if (!confirmed) return;

    fetch(`/api/item/${id}`, { method: "DELETE" })
      .then((res) => res.json())
      .then((data) => {
        if (data.message) {
          showMessage(data.message, "green");
          getItems();
        } else {
          showMessage("Item not found or already deleted", "red");
        }
      })
      .catch((err) => {
        showMessage("Error deleting item", "red");
        console.error("Delete error:", err);
      });
  });

// Display message
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
