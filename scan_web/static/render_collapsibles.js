function toggleCollapseNext(event) {
    console.log("toggled!");
    var next = event.target.nextElementSibling;
    console.log(event.target);
    if (next.style.display === "none") {
        next.style.display = "";
        event.target.innerText = "▼ " + event.target.innerText.substring(1)
    } else {
        next.style.display = "none";
        event.target.innerText = "▶" + event.target.innerText.substring(1);
    }
}

// These are headings that, when clicked, should have their next sibling's display set to none
var collapsibles = document.getElementsByClassName("collapsible");
for (i = 0; i < collapsibles.length; i++) {
    if (!collapsibles[i].innerText.startsWith("▶")) {
        collapsibles[i].innerText = "▶ " + collapsibles[i].innerText;
    }
    collapsibles[i].nextElementSibling.style.display = "none";
    collapsibles[i].addEventListener("click", toggleCollapseNext);
}