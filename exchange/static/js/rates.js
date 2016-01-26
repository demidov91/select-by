$(document).ready(function(){
        $("table").tablesorter({
            headers: {
                0: {sorter:false}
            },
            sortList: [[2, 0]]
        });
});