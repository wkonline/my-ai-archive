//时间选择器格式显示
$(document).ready(function () {
    $('#id_date').datepicker({
        weekStart: 1,
        autoclose: true,
        daysOfWeekHighlighted: "0,6",
        format: "yyyy-mm-dd",
        language: "zh-CN"
    }).datepicker("setDate",'now');
});
$(document).ready(function () {
    $('#id_effective_date').datepicker({
        weekStart: 1,
        autoclose: true,
        daysOfWeekHighlighted: "0,6",
        format: "yyyy-mm-dd",
        language: "zh-CN"
    }).datepicker("setDate",'now');
});
$(document).ready(function () {
    $('#id_delivery_date').datepicker({
        weekStart: 1,
        autoclose: true,
        daysOfWeekHighlighted: "0,6",
        format: "yyyy-mm-dd",
        language: "zh-CN"
    }).datepicker("setDate",'now');
});