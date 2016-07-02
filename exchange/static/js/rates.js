function getFloat(id){
	return parseFloat($('#' + id).val());
}

function getFloatFromText(id){
	return parseFloat($('#' + id).text());
}

// Lets consider that 3-3.1 for 100 RUB is good rate for BYN.
var minRubRate = 0.03;
var maxRubRate = 0.031;
var slowDownCoefficient = 0.5;

function updateData(){
	if ($('#count-nbrb')[0].checked){
		var prevNbrb = getFloatFromText('prev-nbrb');
		var prevRub = prevNbrb / getFloatFromText('prev-rub');
		var currentRub = getFloat('current-rub');
		var rubChange = currentRub / prevRub;

		var nextNbrb = (prevNbrb * (1 + (rubChange - 1) * slowDownCoefficient)).toFixed(4);
		var nextRub = prevRub * (1 - slowDownCoefficient) * rubChange;

		if (((nextRub > maxRubRate) && (rubChange > 1)) || ((nextRub < minRubRate) && (rubChange < 1))){
			nextNbrb = (prevNbrb * rubChange).toFixed(4);
		}

        if (currentRub != NaN){
            $('#predict-line').removeClass('up down').addClass(currentRub > prevRub ? 'up' : 'down');
        }
		$('#next-nbrb').val(nextNbrb);
	}
	var nextNbrb = getFloat('next-nbrb');
    var sellAt = (nextNbrb * (1 + getFloat('exchange-sell-to-nbrb') / 100)).toFixed(4);
    var buyAt = (nextNbrb / (1 + getFloat('exchange-buy-to-nbrb') / 100)).toFixed(4);
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
        url: 'https://query.yahooapis.com/v1/public/yql?q=select+*+from+yahoo.finance.xchange+where+pair+=+%22USDRUB%22&format=json&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys',
        jsonp: "callback",
        dataType: "jsonp",
        success: function(data){
            $('#current-rub').val(data['query']['results']['rate']['Rate']);
            var rubTime = data['query']['results']['rate']['Time'].slice(0, - 2) + ' ' + data['query']['results']['rate']['Time'].slice(-2);
            var rubDateTime = data['query']['results']['rate']['Date'] + ' ' + rubTime + ' UTC';
            $('#current-rub-time').text(formatDateTime(new Date(rubDateTime)));
            updateData();  
        }
    });

    $('#prev-nbrb, #prev-rub, #current-rub, #next-nbrb, #exchange-buy-to-nbrb, #exchange-sell-to-nbrb').keyup(updateData);
    $('#count-nbrb').change(updateData);
});
