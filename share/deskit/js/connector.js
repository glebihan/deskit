function Connector(box_id){
    this._init(box_id);
}

Connector.prototype = {
    _init: function(box_id){
        this._box_id = box_id;
        this._event_callbacks = {};
    },
    
    connect: function(event_name, callback){
        if (!(event_name in this._event_callbacks)) this._event_callbacks[event_name] = new Array();
        this._event_callbacks[event_name].push(callback);
    },
    
    emit: function(event_name, data){
        if (event_name in this._event_callbacks){
            for (var i in this._event_callbacks[event_name]){
                this._event_callbacks[event_name][i](data);
            }
        }
    }
}
