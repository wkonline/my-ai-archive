$(function () {
    function fmtDate(d) {
        return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
    }

    function insertQuickDates($form) {
        var df = $form.find('input[name="date_from"],input[name="start_date"]').first();
        var dt = $form.find('input[name="date_to"],input[name="end_date"]').first();
        if (!df.length || !dt.length) {
            return;
        }

        var today = new Date();
        var currentMonthStart = new Date(today.getFullYear(), today.getMonth(), 1);
        var currentQuarterStart = new Date(today.getFullYear(), Math.floor(today.getMonth() / 3) * 3, 1);
        var currentYearStart = new Date(today.getFullYear(), 0, 1);

        var buttons = [
            {label: '本月', from: currentMonthStart, to: today},
            {label: '本季度', from: currentQuarterStart, to: today},
            {label: '本年度', from: currentYearStart, to: today},
        ];

        var $bar = $('<div class="quick-date-bar"></div>');
        $.each(buttons, function (i, item) {
            var $btn = $('<button type="button" class="btn btn-xs btn-default quick-date-btn"></button>').text(item.label);
            $btn.on('click', function () {
                df.val(fmtDate(item.from));
                dt.val(fmtDate(item.to));
            });
            $bar.append($btn);
        });

        var $targetRow = $form.children('.row').first();
        if ($targetRow.length) {
            var $dateField = $form.find('.quick-date-anchor').first();
            if (!$dateField.length) {
                $dateField = $form.find('input[name="date_to"],input[name="end_date"]').closest('[class*="col-"]').first();
            }
            if ($dateField.length) {
                $dateField.append($bar);
            } else {
                $targetRow.before($bar);
            }
        } else {
            $form.prepend($bar);
        }
    }

    $('form[method="get"]').each(function () {
        var $form = $(this);
        if ($form.find('input[name="date_from"],input[name="start_date"],input[name="date_to"],input[name="end_date"]').length) {
            insertQuickDates($form);
        }
    });
});
