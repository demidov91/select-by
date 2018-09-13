ymaps.ready(initMap);

function initMap() {
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
        for (var point of data.exchange){
            map.geoObjects.add(externalDataToPoint(point));
        }        
    });

    configMapRelatedBehaviour(map);
}

function configMapRelatedBehaviour(map){
    map.geoObjects.events.add('click', onPointClick);

    $(".clear-points").click(function(event){
        for (point in map.geoObjects){
            turnPointOff(point);
        }
    });
}

function onPointClick(event){
    var point = event.get('target');
    if (point.properties.get('isSelected')){
        turnPointOff(point);
    } else {
        turnPointOn(point);
    }
}

function turnPointOff(point){
    point.properties.set('isSelected', false);
    point.options.set('preset', 'islands#grayIcon');
    return point;
}

function turnPointOn(point){
    point.properties.set('isSelected', true);
    point.options.set('preset', 'islands#darkGreenIcon');
    return point;
}

function externalDataToPoint(externalPoint){    
    if (externalPoint.isSelected){
        return new ymaps.Placemark(
            x.coordinates,
            {
                isSelected: true,
                iconContent: externalPoint.content
            },
            {
                preset: 'islands#darkGreenIcon'
            }      
        );
    }

    return new ymaps.Placemark(
        externalPoint.coordinates,
        {
            isSelected: false,
            content: externalPoint.content
        },
        {
            preset: 'islands#grayIcon'
        }      
    );    
}
