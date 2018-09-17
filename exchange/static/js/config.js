ymaps.ready(initMap);

var allPoints = null;

function initMap() {
    var map = new ymaps.Map("map", {
        center: [53.902257, 27.561831],
        zoom: 12
    }, {
        searchControlProvider: 'yandex#search'
    });

    $.ajax({
        url: "/my-points/",
        method: "GET",
        dataType: "json"
    }).done(function(data){
        allPoints = new ymaps.geoQuery(data.exchange.map(externalDataToPoint));
        allPoints.addToMap(map);
        configMapRelatedBehaviour(map);        
    });

    
}

function configMapRelatedBehaviour(map){
    allPoints.addEvents('click', onPointClick);
    map.events.add('click', onMapClick);

    $(".js-clear").click(function(event){
        allPoints.each(turnPointOff);        
    });    

    $('.js-save').click(onSave);
}

function onPointClick(event){
    var point = event.get('target');
    if (point.properties.get('isSelected')){
        turnPointOff(point);
    } else {
        turnPointOn(point);
    }
}

function onMapClick(event){
    var map  = event.get('target');
    var coordinates = event.get('coords');
    
    var circle = new ymaps.Circle([coordinates, 1000]);
    map.geoObjects.add(circle);
    var pointsToAdd = allPoints.searchInside(circle);
    pointsToAdd.each(turnPointOn); 
    map.geoObjects.remove(circle);   
}

function onSave(event){
    var points = allPoints.search('properties.isSelected=true');
    var points_id = points._objects.map(function(x){return x.properties.get('id');});
    var online_id = $.map($('[name=online]:checked'), (function(x){return x.value;}));

    var data = {
        'points': points_id.concat(online_id)
    }; 

    $.ajax({
        url: '/save-points/',
        method: 'POST',
        data: data
    }).done(function(e){
        window.location.href = '/';
    });
}

function turnPointOff(point){
    point.properties.set('isSelected', false);
    point.options.set('preset', 'islands#grayDotIcon');
    return point;
}

function turnPointOn(point){
    point.properties.set('isSelected', true);
    point.options.set('preset', 'islands#darkGreenStretchyIcon');
    return point;
}

function externalDataToPoint(externalPoint){    
    if (externalPoint.isSelected){
        return new ymaps.Placemark(
            externalPoint.coordinates,
            {
                id: externalPoint.id,
                isSelected: true,
                iconContent: externalPoint.content
            },
            {
                preset: 'islands#darkGreenStretchyIcon'
            }      
        );
    }

    return new ymaps.Placemark(
        externalPoint.coordinates,
        {
            id: externalPoint.id,
            isSelected: false,
            iconContent: externalPoint.content
        },
        {
            preset: 'islands#grayDotIcon'
        }      
    );    
}
