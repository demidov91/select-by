ymaps.ready(initMap);

var allPoints = null;
var clusterSelected = null;
var clusterNotSelected = null;

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
        var barePlacemarks = data.exchange.map(externalDataToPoint);
        
        allPoints = new ymaps.geoQuery(barePlacemarks);
        allPoints.addToMap(map);

        enableClusterization(map, barePlacemarks);

        configMapRelatedBehaviour(map);        
    });
}

function configMapRelatedBehaviour(map){
    allPoints.addEvents('click', onPointClick);
    
    $(".js-clear").click(function(event){
        allPoints.each(turnPointOff);        
    });    

    $('.js-save').click(onSave);

    map.events.add('boundschange', function(event) {
        if (event.get('newZoom') !== event.get('oldZoom')) {
            var stopZoom = event.get('newZoom') > 12;
            console.log(stopZoom);

            clusterSelected.options.set('clusterDisableClickZoom', stopZoom);
            clusterNotSelected.options.set('clusterDisableClickZoom', stopZoom);        
        }

    });
}


function enableClusterization(map, placemarks){
    var selected = [];
    var notSelected = [];

    for (var x of placemarks){
        if (x.properties.get('isSelected')){
            selected.push(x);
        } else {
            notSelected.push(x);
        }
    }

    clusterSelected = new ymaps.Clusterer({
        gridSize: 256, 
        preset: 'islands#darkGreenClusterIcons'
    });
    clusterSelected.add(selected);

    clusterNotSelected = new ymaps.Clusterer({
        gridSize: 256, 
        preset: 'islands#grayClusterIcons',
    });

    clusterNotSelected.add(notSelected);

    map.geoObjects.add(clusterSelected);
    map.geoObjects.add(clusterNotSelected);
}

function onPointClick(event){
    var point = event.get('target');
    if (point.properties.get('isSelected')){
        turnPointOff(point);
    } else {
        turnPointOn(point);
    }
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
    clusterSelected.remove(point);
    clusterNotSelected.add(point);
    return point;
}

function turnPointOn(point){
    point.properties.set('isSelected', true);
    point.options.set('preset', 'islands#darkGreenStretchyIcon');
    clusterSelected.add(point);
    clusterNotSelected.remove(point);
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
