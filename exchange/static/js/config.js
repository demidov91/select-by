$(function(){
    $('#filter-list').keyup(function(){
        var searchForPhrase = this.value;
        $('#id_exchange_offices li').css('display', 'block').filter(function(){
            return !$(this).text().contains(searchForPhrase);
        }).css('display', 'none');
    });
    $('#filter-list').keyup();
});