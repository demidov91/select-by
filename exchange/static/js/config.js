ymaps.ready(initMap);

var allPoints = null;
var clusterSelected = null;
var clusterNotSelected = null;
var needClusterUpdate = false;

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

    $('body').on('click', '.js-editor-balloon--item', onClusterItemClick);
    $('body').on('click', '.js-editor-balloon--all-action', onChangeAllBalloonPoints);  
}


function enableClusterization(map, placemarks){
    var selNotSel = getSelectedNotSelected(placemarks);
    var selected = selNotSel[0];
    var notSelected = selNotSel[1];

    var CUSTOM_BALOON = ymaps.templateLayoutFactory.createClass([
        '<div class="editor-balloon--header editor-balloon--button h5">', 
            '🔍 Приблизить', 
        '</div>',
        '<div class="editor-balloon--items js-editor-balloon--items">',
        '{% for point in properties.geoObjects %}',
            '<div data-id="{{ point.properties.id }}" ',
                'class="', 
                    'js-editor-balloon--item ', 
                    'editor-balloon--item ', 
                    'editor-balloon--button ',
                    'h5 ',                     
                    '{% if point.properties.isSelected %}editor-balloon--item-selected{% else %}editor-balloon--item-not-selected{% endif %}"',
            '>',
                '{{ point.properties.bank }}: {{ point.properties.address }}',
            '</div>',
        '{% endfor %}',
        '</div>',
        '<div class="js-editor-balloon--mass-action-row">',
            '<div ', 
                'class="col-xs-6 editor-balloon--button js-editor-balloon--all-action h5 "', 
                'data-action="on"',
            '><nobr>✅ Выбрать все</nobr></div>',     
            '<div ', 
                'class="col-xs-6 editor-balloon--button js-editor-balloon--all-action h5"', 
                'data-action="off"',
            '><nobr>Отменить все ❌</nobr></div>',     
        '</div>',
    ].join(''));

    var clusterOptions = {
        gridSize: 256, 
        clusterBalloonContentLayout: CUSTOM_BALOON,
        clusterIconLayout: 'default#pieChart'
    };

    clusterSelected = new ymaps.Clusterer(clusterOptions);
    clusterNotSelected = new ymaps.Clusterer(clusterOptions);

    clusterSelected.options.set('isSelected', true);
    clusterNotSelected.options.set('isSelected', false);

    clusterNotSelected.add(notSelected);
    clusterSelected.add(selected);

    clusterNotSelected.createCluster = overridenCreateCluster;
    clusterSelected.createCluster = overridenCreateCluster;

    map.geoObjects.add(clusterSelected);
    map.geoObjects.add(clusterNotSelected);

    map.events.add('boundschange', function(event){
        if (event.get('oldZoom') == event.get('newZoom')){
            return;
        }
        if (!needClusterUpdate){
            return;
        }
        updateClusters();
        needClusterUpdate = false;
    });
}

function overridenCreateCluster(center, geoObjects){
    var newCluster = ymaps.Clusterer.prototype.createCluster.call(
        this, 
        center, 
        geoObjects
    );
    newCluster.options.set('disableClickZoom', geoObjects.length < 10);
    return newCluster;
};

function onPointClick(event){
    var point = event.get('target');
    if (point.properties.get('isSelected')){
        turnPointOff(point);
    } else {
        turnPointOn(point);
    }
}

function onClusterItemClick(event){
    var $this = $(this);
    var switchTo = !$this.hasClass('editor-balloon--item-selected');    
    changeBalloonItem($this, switchTo);
}

function onChangeAllBalloonPoints(event){
    var $button = $(event.target).parents('.js-editor-balloon--all-action');
    var switchTo = $button.data('action') == 'on';   
    
    $items = $button.parents(
        '.js-editor-balloon--mass-action-row'
    ).siblings(
        '.js-editor-balloon--items'
    ).find(
        '.js-editor-balloon--item'
    ).each(function(x){
        changeBalloonItem(
            $(this), switchTo
    )});
}

function changeBalloonItem($item, switchTo){
    var point = allPoints.search(
        'properties.id=' + $item.data('id')
    )._objects[0];

    if (switchTo){
        turnPointOn(point, modifyClusters=false);
        $item.removeClass(
            'editor-balloon--item-not-selected'
        ).addClass(
            'editor-balloon--item-selected'
        );
    } else {
        turnPointOff(point, modifyClusters=false);
        $item.removeClass(
            'editor-balloon--item-selected'
        ).addClass(
            'editor-balloon--item-not-selected'
        );
    };
    needClusterUpdate = true;
}

function updateClusters(){
    clusterNotSelected.removeAll();
    clusterSelected.removeAll();

    var selNotSel = getSelectedNotSelected(allPoints._objects);

    clusterSelected.add(selNotSel[0]);
    clusterNotSelected.add(selNotSel[1]);
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

function turnPointOff(point, modifyClusters=true){
    point.properties.set('isSelected', false);
    point.options.set('preset', 'islands#greyStretchyIcon');
    if (modifyClusters){
        clusterSelected.remove(point);
        clusterNotSelected.add(point);
    }
    return point;
}

function turnPointOn(point, modifyClusters=true){
    point.properties.set('isSelected', true);
    point.options.set('preset', 'islands#darkGreenStretchyIcon');
    if (modifyClusters){
        clusterSelected.add(point);
        clusterNotSelected.remove(point);
    }
    return point;
}

function externalDataToPoint(externalPoint){   
    var point = new ymaps.Placemark(
        externalPoint.coordinates,
        {
            id: externalPoint.id,
            isSelected: externalPoint.isSelected,
            iconContent: externalPoint.content,
            address: externalPoint.address,
            bank: externalPoint.bank,
        }   
    );
    
    if (externalPoint.isSelected){
        point.options.set('preset', 'islands#darkGreenStretchyIcon'); 
    } else {
        point.options.set('preset', 'islands#greyStretchyIcon'); 
    }

    return point;
}

// Returns a list with 2 items: 
//     list of selected points and list of not selected placemarks.
function getSelectedNotSelected(placemarks){
    var selected = [];
    var notSelected = [];

    for (var x of placemarks){
        if (x.properties.get('isSelected')){
            selected.push(x);
        } else {
            notSelected.push(x);
        }
    }
    return [selected, notSelected];
}