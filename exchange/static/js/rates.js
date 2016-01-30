function getFloat(id){
	return parseFloat($('#' + id).val());
}


function updateData(){
	if ($('#count-nbrb')[0].checked){
		var prevNbrb = getFloat('prev-nbrb');
		var prevRub = prevNbrb / getFloat('prev-rub');
		var currentRub = getFloat('current-rub');
		$('#next-nbrb').val(Math.round(prevNbrb * (1 + (currentRub / prevRub - 1) / 2)));
	}
	var nextNbrb = getFloat('next-nbrb');
	$('#sell-at').text(Math.round(nextNbrb * (1 + getFloat('exchange-sell-to-nbrb') / 100)));
	$('#buy-at').text(Math.round(nextNbrb / (1 + getFloat('exchange-buy-to-nbrb') / 100)));
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
            $('#prev-nbrb').val(data['USD']);    
            $('#prev-rub').val(data['RUB']);  
            updateData();   
        }
    });
    $.ajax({
        url: 'https://query.yahooapis.com/v1/public/yql?q=select+*+from+yahoo.finance.xchange+where+pair+=+%22USDRUB%22&format=json&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys&callback=',
        success: function(data){
            $('#current-rub').val(data['query']['results']['rate']['Rate']);
            $('#current-rub-time').text('(' + data['query']['results']['rate']['Date'] + ' ' + data['query']['results']['rate']['Time'] + ' UTC)');
            updateData();  
        }
    });

    $('#prev-nbrb, #prev-rub, #current-rub, #next-nbrb, #exchange-buy-to-nbrb, #exchange-sell-to-nbrb').keyup(updateData);
    $('#count-nbrb').keyup(updateData);
});
