window.onload = function () {
        timer();
}

function timer() {
        var xmlhttp = new XMLHttpRequest();
        xmlhttp.open("GET", "/query", true);
        xmlhttp.timeout = 2000;
        xmlhttp.onreadystatechange = function(){
                // console.log("xmlhttp.readyState=" + xmlhttp.readyState + " ,xmlhttp.status=" + xmlhttp.status);
                if(xmlhttp.readyState == 4 && xmlhttp.status == 200){
                        obj = JSON.parse(xmlhttp.responseText);
                        console.log(obj["currenttime"]);
                        console.log(obj["currenttime"]);
                        document.getElementById("time").innerHTML = obj["currenttime"];

                        for (var prop in obj["state"]) {
                                // console.log(prop + " " + obj["state"][prop]);
                                e = document.getElementById(prop);
                                e.classList.remove("on");
                                e.classList.remove("off");
                                e.classList.add(obj["state"][prop] ? "on" : "off");
                        }
                        setTimeout(timer, 1000);
                }
        }
        xmlhttp.send();
}
