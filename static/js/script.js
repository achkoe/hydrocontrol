window.onload = function () {
        console.log('DOC loaded');
        timer();
}

function timer() {
        // console.log("timer");
        var xmlhttp = new XMLHttpRequest();
        xmlhttp.open("GET", "/query", true);
        xmlhttp.timeout = 200;
        xmlhttp.onreadystatechange = function(){
            if(xmlhttp.readyState == 4 && xmlhttp.status == 200){
                console.log(xmlhttp.responseText);
                obj = JSON.parse(xmlhttp.responseText);
                for (var prop in obj) {
                        e = document.getElementById(prop);
                        e.classList.remove("on");
                        e.classList.remove("off");
                        e.classList.add(obj[prop] ? "on" : "off");
                }
                setTimeout(timer, 1000);
            }
        }
        xmlhttp.send();
}
