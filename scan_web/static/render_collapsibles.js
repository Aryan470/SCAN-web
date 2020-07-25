function toggleCollapseNext(event) {
    var label = event.target;
    if (label.tagName === "I") {
        label = label.parentElement;
    }

    var currDir = label.firstElementChild.classList[1];
    if (currDir === "right") {
        label.firstElementChild.classList = "arrow down";
    } else {
        label.firstElementChild.classList = "arrow right";
    }
    var next = label.nextElementSibling;
    if (next.style.display === "none") {
        next.style.display = "";
    } else {
        next.style.display = "none";
    }
}

// These are headings that, when clicked, should have their next sibling's display set to none
var collapsibles = document.getElementsByClassName("collapsible");
for (i = 0; i < collapsibles.length; i++) {
    collapsibles[i].innerText = " " + collapsibles[i].innerText;
    var newArrow = document.createElement("i");
    newArrow.classList = "arrow right"
    collapsibles[i].prepend(newArrow);

    collapsibles[i].nextElementSibling.style.display = "none";
    collapsibles[i].addEventListener("click", toggleCollapseNext);
}