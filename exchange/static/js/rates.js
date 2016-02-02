function getFloat(id){
	return parseFloat($('#' + id).val());
}

function getFloatFromText(id){
	return parseFloat($('#' + id).text());
}



function updateData(){
	if ($('#count-nbrb')[0].checked){
		var prevNbrb = getFloatFromText('prev-nbrb');
		var prevRub = prevNbrb / getFloatFromText('prev-rub');
		var currentRub = getFloat('current-rub');
        var nextNbrb = Math.round(prevNbrb * currentRub / prevRub);
        if (currentRub != NaN){
            $('#predict-line').removeClass('up down').addClass(currentRub > prevRub ? 'up' : 'down');
        }
		$('#next-nbrb').val(nextNbrb);
	}
	var nextNbrb = getFloat('next-nbrb');
    var sellAt = Math.round(nextNbrb * (1 + getFloat('exchange-sell-to-nbrb') / 100));
    var buyAt = Math.round(nextNbrb / (1 + getFloat('exchange-buy-to-nbrb') / 100));
	$('#sell-at').text(sellAt);
	$('#buy-at').text(buyAt);
}

function prependZeroTo2(value){
    return ('00'+value).slice(-2);
}

function formatDate(date){
    return prependZeroTo2(date.getDate()) + '.' + prependZeroTo2((date.getMonth() + 1)) + '.' + (date.getYear() + 1900);
}

function formatDateTime(datetime){
     return formatDate(datetime) + ' ' + prependZeroTo2(datetime.getHours()) + ':' + prependZeroTo2(datetime.getMinutes());
}

$(document).ready(function(){
    $("table").tablesorter({
        headers: {
            0: {sorter:false}
        },
        sortList: [[2, 0]]
    });

    $.ajax({
        url: $('#counter-data').data('nbrb-rates'),
        success: function(data){
            $('#prev-nbrb').text(data['USD']);    
            $('#prev-rub').text(data['RUB']);  
            $('#nbrb-time').text(formatDate(new Date(data['for_date'])));
            updateData();   
        }
    });
    $.ajax({
        url: 'https://query.yahooapis.com/v1/public/yql?q=select+*+from+yahoo.finance.xchange+where+pair+=+%22USDRUB%22&format=json&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys&callback=',
        success: function(data){
            $('#current-rub').val(data['query']['results']['rate']['Rate']);
            var rubTime = data['query']['results']['rate']['Time'].slice(0, - 2) + ' ' + data['query']['results']['rate']['Time'].slice(-2);
            var rubDateTime = data['query']['results']['rate']['Date'] + ' ' + rubTime + ' UTC';
            $('#current-rub-time').text(formatDateTime(new Date(rubDateTime)));
            updateData();  
        }
    });

    $('#prev-nbrb, #prev-rub, #current-rub, #next-nbrb, #exchange-buy-to-nbrb, #exchange-sell-to-nbrb').keyup(updateData);
    $('#count-nbrb').keyup(updateData);
});
