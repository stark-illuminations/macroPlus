function changeMacroEditor(uuid) {
    const macroEditor = document.getElementById("macro_editor")
    const macroList = document.getElementById("macro_list")
    for (const child of macroEditor.children) {
        if (child.nodeName == "DIV" && !(child.classList.contains("hidden"))) {
            child.classList.add("hidden")
        }
        if (child.id.includes(uuid)) {
            child.classList.remove("hidden")
        }
    }
    for (const child of macroList.children) {
        if (child.nodeName == "DIV" && child.classList.contains("selected")) {
            child.classList.remove("selected")
        }
        if (child.id.includes(uuid)) {
            child.classList.add("selected")
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
   const macroButtons = document.getElementById("macro_list")
   for (const child of macroButtons.children) {
        if (child.nodeName == "DIV") {
            child.addEventListener('click', function() {
              // specify the action to take when the div is clicked
              changeMacroEditor(child.id)
            })
        }
   }
}, false)