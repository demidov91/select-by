ymaps.ready(init);

function init() {
    var map = new ymaps.Map("map", {
        center: [53.902257, 27.561831],
        zoom: 11
    }, {
        searchControlProvider: 'yandex#search'
    });

    $.ajax({
        url: "/my-points/",
        method: "GET",
        dataType: "json"
    }).done(function(data){
        var points = data["exchange"];
        var my_places = data["my_places"];

        var ya_points = ymaps.geoQuery(
            points.map(function(x){
                return {
                    coordinates: x.coordinates,
                    type: 'Point',                
                }
            })
        );

        ya_points.addToMap(map);
    });
}
