$(function(){
    $('#filter-list').keyup(function(){
        var searchForPhrases = this.value.toLowerCase().split(/[^\w(А-я)(І-ў)]+/);
        $('#id_exchange_offices li').css('display', 'block').filter(function(){
            var currentLine = $(this).text().toLowerCase();
            for (i in searchForPhrases){
                if (!currentLine.contains(searchForPhrases[i])){
                    return true;
                }
            }
            return false;
        }).css('display', 'none');
    });
    $('#filter-list').keyup();
});