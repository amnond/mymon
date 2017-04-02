
function map2array(map, idxname)
{
    if (typeof map != "object") {
        return null;
    }
    var arr = [];
    for (key in map) {
        var obj = JSON.parse(JSON.stringify(map[key]));
        obj[idxname] = key;
        arr.push(obj);
    }
    return arr;
}

function array2map(arr, idxname)
{
    if ( Object.prototype.toString.call( arr ) !== '[object Array]' ) {
        return null
    }
    var map = {};
    for (var i=0; i<arr.length; i++) {
        var obj = JSON.parse(JSON.stringify(arr[i]));
        if (!(idxname in obj)) {
            console.log("error: "+idxname+" not found in obj", obj);
            continue;
        }
        if (idxname in map) {
            console.log("error: " + idxname + " already in map", map[idxname]);
            continue;
        }
        map[obj[idxname]] = obj;
        // delete obj[indexname];
    }
    return map;
}
