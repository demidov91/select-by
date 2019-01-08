function getFloat(selector){
	return parseFloat($(selector).val());
}

function getFloatFromText(id){
	return parseFloat($('#' + id).text());
}

// Lets consider that 3.1-3.3 for 100 RUB is good rate for BYN.
var minRubRate = 3.1;
var maxRubRate = 0.033;
var slowDownCoefficient = 0.5;
var prevUsd = getFloatFromText('prev-usd');

function updateData(){		
	var prevRub = prevUsd / getFloatFromText('prev-rub');
	var currentRub = getFloat('.js-current-rub');
	var rubChange = currentRub / prevRub;

	var nextNbrb = (prevUsd * (1 + (rubChange - 1) * slowDownCoefficient)).toFixed(4);
	var nextRubByn = nextNbrb / (prevRub*rubChange);

	if (((nextRubByn > maxRubRate) && (rubChange > 1)) || ((nextRubByn < minRubRate) && (rubChange < 1))){
		nextNbrb = (prevUsd * rubChange).toFixed(4);
	}

    if (currentRub != NaN){
        $('#predict-line').removeClass('up down').addClass(currentRub > prevRub ? 'up' : 'down');
    }
	$('.js-next-nbrb').text(nextNbrb);
    $('#prev-usd-rub').text(prevRub.toFixed(2));
}

function prependZeroTo2(value){
    return ('00'+value).slice(-2);
}

function formatDate(date){
    return prependZeroTo2(date.getDate()) + '.' + prependZeroTo2((date.getMonth() + 1)) + '.' + (date.getYear() + 1900);
}

$(document).ready(function(){
    $("table").tablesorter({
        headers: {
            0: {sorter:false}
        },
        sortList: [[2, 0]]
    });
    $.ajax({
        url: 'https://free.currencyconverterapi.com/api/v5/convert?q=USD_RUB&compact=y',
        method: 'GET',
        success: function(data){
            $('.js-current-rub').val(data['USD_RUB']['val']);
            updateData();  
        }
    });
    $('#nbrb-time').text(formatDate(new Date($('#nbrb-time').text())));
    $('.js-current-rub').keyup(updateData);
    $('.js-office').click(function(){
        window.open($(this).data('href'), '_blank');
    });

});
