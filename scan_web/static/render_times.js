var dates = document.getElementsByClassName("date");
var times = document.getElementsByClassName("time");
var datetimes = document.getElementsByClassName("datetime");
for (i = 0; i < dates.length; i++) {
    var thisDate = moment.utc(dates[i].innerHTML).local();
    dates[i].innerHTML = thisDate.format("M/D");
}
for (i = 0; i < times.length; i++) {
    var thisTime = moment(times[i].innerHTML);
    times[i].innerHTML = thisTime.format("h:mm A");
}
for (i = 0; i < datetimes.length; i++) {
    var thisDateTime = moment(datetimes[i].innerHTML);
    datetimes[i].innerHTML = thisDateTime.format("M/D h:mm A");
}