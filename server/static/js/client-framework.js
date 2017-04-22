function get_framework(params) {
    var globals = {};
    var obj = {};

    obj.del_global = function(key) {
        if (key in globals) {
            delete globals[key];
            return true;
        }
        return false;
    };

    obj.get_global = function(key) {
        return (key in globals) ? globals[key] : null
    };

    obj.set_global = function(key, val) {
        globals[key] = val;
    };

    obj._postRequest = function( jsonData, callback ) {
        var url = '/ajax'
        var jsonStr = JSON.stringify( jsonData );
        $('#idreq').val( jsonStr );
        $.post( url,
                $('#reqform').serialize(),
                callback,
                //"application/json" );
                "text" );
    };

    obj.postRequestSilent = function( jsonData, callback ) {
        obj._postRequest(jsonData, callback);
    };

    obj.postRequest = function( jsonData, callback ) {
        obj.show_wait()
        obj._postRequest(jsonData, function(data) {
            obj.hide_wait()
            if (typeof(callback)=='function') {
                callback(data);
            }
        });
    };

    obj.load = function(page) {
        if ('on_view_unloading' in window &&
            typeof window.on_view_unloading == 'function' ) {
            on_view_unloading();
            delete window.on_view_unloading;
        }
        $( '#pageview' ).hide();   // hide current page view
        $( '#loading' ).show()     // show animation until new page is received
        $( "#pageview" ).load( "/"+page+".html", function() {  // request relevant page
            $( '#loading' ).hide()   // when received, hide wait animation
            $( '#pageview' ).show(); // and show newly arrive page
        });
    }

    obj.show_wait = function() {
        $('#waitmodal').modal('show')
    }

    obj.hide_wait = function() {
        $('#waitmodal').modal('hide')
    }

    obj.request_connection = function(service, conn) {
        var inservice = false;

        if (typeof(conn) != "object") {
            console.log("Error: connection parameter has to be an object")
            return;
        }

        conn.send = function(data) {
            console.log('attempting to send on invalid connection');
        }

        if ("MozWebSocket" in window) {
            WebSocket = MozWebSocket;
        }

        if (WebSocket) {
            var req = {service:service}
            var sreq = JSON.stringify(req);
            var ws = new WebSocket(params.ws_url);
            conn.close = function() {
                ws.onclose = function () {}; // disable onclose handler first
                ws.close()
            }
            ws.onopen = function () { ws.send(sreq) };
            ws.onmessage = function(evt) {
                //console.log(evt);
                var data = evt.data;
                if (!inservice) {
                    var stat = 'error'
                    var response = {};
                    try {
                        response = JSON.parse(data);
                        stat = response.status;
                        if (response.service == service && stat == 'ok') {
                            inservice = true;
                            conn.send = function(data) {
                                // connect the send method directly to the websocket send
                                ws.send(data);
                            }
                        }
                    }
                    catch (e) {
                        console.log(e);
                    }
                    if (!('onConnectAck' in conn)) {
                        console.log('Error: connection has no onConnectAck method');
                        return;
                    }

                    conn.onConnectAck(stat)
                    return;
                }
                if (!('onData' in conn)) {
                    console.log('Error: connection has no onData method');
                    return;
                }
                conn.onData(data);
            }
            ws.onclose = function () {
                if (inservice) {
                    if (!('onClose' in conn)) {
                        console.log('Error: connection has no onClose method');
                        return;
                    }
                    conn.onClose();
                }
                console.log("websock closed")
            };
        }
        else {
            console.log("WebSocket not supported");
        }
    };

    return obj;
}