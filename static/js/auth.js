$( document ).ready(function() {
	$("#registration-form").submit(function(e) {
		e.preventDefault();
		var url = $("#registration-form").attr("action");
		var xhr = $.ajax({
			type: "POST",
			url: url,
			data: $("#registration-form").serialize(),
			success: function(data)
			{
				if (xhr.getResponseHeader("Content-Type") == 'application/json') {
					window.location.href = data['url'];
				} else {
					$("#registration-form").html(data);

					$.UIkit.domObserve('#registration-form', function(element) { 
					 });
				}
			}
		})
	});

	$("#login-form").submit(function(e) {
		e.preventDefault();
		var url = $("#login-form").attr("action");
		var xhr = $.ajax({
			type: "POST",
			url: url,
			data: $("#login-form").serialize(),
			success: function(data)
			{
				if (xhr.getResponseHeader("Content-Type") == 'application/json') {
					window.location.href = data['url'];
				} else {
					$("#login-form").html(data);

					$.UIkit.domObserve('#login-form', function(element) { 
					 });
				}
			}
		})
	});

});
