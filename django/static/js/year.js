// Get the current year
const year = (new Date).getFullYear();

// Replace $YEAR in the title
document.title = document.title.replace("$YEAR", String(year))

// Fill all .year elements with the current year
const elements = document.getElementsByClassName("year");
// Array.prototype.forEach is needed since you cannot loop over HTMLCollections normally
Array.prototype.forEach.call(elements, element => {
    element.innerText = year;
})