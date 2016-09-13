function getFloat(id){
	return parseFloat($('#' + id).val());
}

function getFloatFromText(id){
	return parseFloat($('#' + id).text());
}

// Lets consider that 3-3.1 for 100 RUB is good rate for BYN.
var minRubRate = 3;
var maxRubRate = 0.031;
var slowDownCoefficient = 0.5;
var exchangeMargin = getFloat('exchange-margin') / 100;
var prevUsd = getFloatFromText('prev-usd');
var prevEur = getFloatFromText('prev-eur');

function updateData(){		
	var prevRub = prevUsd / getFloatFromText('prev-rub');
	var currentRub = getFloat('current-rub');
	var rubChange = currentRub / prevRub;

	var nextNbrb = (prevUsd * (1 + (rubChange - 1) * slowDownCoefficient)).toFixed(4);
	var nextRubByn = nextNbrb / (prevRub*rubChange);

	if (((nextRubByn > maxRubRate) && (rubChange > 1)) || ((nextRubByn < minRubRate) && (rubChange < 1))){
		nextNbrb = (prevUsd * rubChange).toFixed(4);
	}

    if (currentRub != NaN){
        $('#predict-line').removeClass('up down').addClass(currentRub > prevRub ? 'up' : 'down');
    }
	$('#next-nbrb').val(nextNbrb);
    $('#prev-usd-rub').text(prevRub.toFixed(2));

	var nextNbrb = getFloat('next-nbrb');
    var sellAt = (nextNbrb * (1 + exchangeMargin)).toFixed(4);
    var buyAt = (nextNbrb / (1 + exchangeMargin)).toFixed(4);
	$('#sell-at').text(sellAt);
	$('#buy-at').text(buyAt);
}


function updateDepoAdvice(){
    $('#advice, #cant-prevent-loss').addClass('hidden');
    var rp = getFloat('byn-percent');
    var dp = getFloat('foreign-percent');
    var months = parseInt($('#months').val());
    var prevForeignNbrb = $('#plan-foreign-currency').val() == 'usd' ? prevUsd : prevEur;
    var currMax = getFloat('expect-max') / prevForeignNbrb;
    var currMin = getFloat('expect-min') / prevForeignNbrb;

    if (!(rp && dp && months && currMax && currMin)){
        return;
    }

    var foreignIncome = Math.pow(1+dp/1200, months);
    var bynIncome = Math.pow(1+rp/1200, months);

    if (document.getElementById('conversation-loss').checked){
        foreignIncome = foreignIncome * Math.pow(1 - exchangeMargin, 2);
    }
    if (document.getElementById('byn-double').checked){
        rp = rp * (rp / 4800 + 1);
    }
    var foreignPart = Math.NaN;
    var loss = 0;
    if (currMax * foreignIncome <= bynIncome){
        foreignPart = 0;
    } else if (currMin * foreignIncome >= bynIncome){
        foreignPart = 100;
    } else if (bynIncome < (currMax + currMin) / 2 * foreignIncome){
        var data = countForeignPart(bynIncome, foreignIncome, currMin, currMax);
        foreignPart = data.percent;
        loss = data.loss;
    } else if (foreignIncome <=1 ){        
        foreignPart = 0;
        loss = Math.round((1 - bynIncome / currMax) * 100);              
    } else {
        var data = countForeignPart(bynIncome, foreignIncome, currMax, currMin);
        foreignPart = data.percent;
        loss = data.loss;
    }
    $('#byn-advice').text(100 - foreignPart);
    $('#foreign-advice').text(foreignPart);       
    if (loss > 0){
        $('#loss').text(loss);
        $('#cant-prevent-loss').removeClass('hidden');  
    }
    $('#advice').removeClass('hidden');
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

function countForeignPart(bynIncome, foreignIncome, currencyChange, oppositeCurrChange){
    var foreignPart = simplyGetForeignPart(bynIncome, foreignIncome, currencyChange);
    var loss = 0;    
    if (foreignPart > 0 && foreignPart < 1){
        loss = Math.max(getLoss(foreignPart, bynIncome, foreignIncome, oppositeCurrChange), 0);  
        if (loss > 0){
            var oppositForeignPart = normalizeForeignPart(simplyGetForeignPart(bynIncome, foreignIncome, oppositeCurrChange));
            var myLoss = Math.max(getLoss(oppositForeignPart, bynIncome, foreignIncome, currencyChange));
            if (myLoss < loss){
                foreignPart = oppositForeignPart;
                loss = myLoss;
            } 
        }    
    }  
    
    return {
        percent: Math.round(normalizeForeignPart(foreignPart) * 100),
        loss: Math.round(loss)
    };
}

function normalizeForeignPart(fp){
    if (fp > 1){
        return 1;
    } else if (fp < 0){
        return 0;
    }
    return fp;
}


function simplyGetForeignPart(bynIncome, foreignIncome, currencyChange){
    return (bynIncome - Math.max(1, currencyChange))/(bynIncome - currencyChange * foreignIncome); 
}

function getLoss(foreignPart, bynIncome, foreignIncome, currencyChange){
    return (Math.max(1, currencyChange) - (foreignPart * (currencyChange * foreignIncome - bynIncome) + bynIncome)) * 100;
}


$(document).ready(function(){
    $("table").tablesorter({
        headers: {
            0: {sorter:false}
        },
        sortList: [[2, 0]]
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
    $('#nbrb-time').text(formatDate(new Date($('#nbrb-time').text())));
    $('#prev-usd, #prev-eur, #prev-rub, #current-rub, #next-nbrb, #exchange-buy-to-nbrb, #exchange-sell-to-nbrb').keyup(updateData);
    $('#depo-planner input').keyup(updateDepoAdvice);
    $('#depo-planner input[type="checkbox"]').change(updateDepoAdvice);
    $('#deposit-planner-question').tooltip();
});
