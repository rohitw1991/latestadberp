wn.pages['dashboard-1'].onload = function(wrapper) { 
	wn.ui.make_app_page({
		parent: wrapper,
		title: 'Dashboard',
		single_column: true
	});
	//var r=documnet.getelemenntsbyclassname('layout-main')
	$('.layout-main').append('<html><head>\
		<script type="application/javascript" src="files/awesomechart.js"> </script>\
                 </head>\
		<body>\
		<div class="chart_container_centered">\
            <canvas id="chartCanvas19" width="600" height="400">\
                Your web-browser does not support the HTML 5 canvas element.\
            </canvas>\
	<script type="application/javascript">\
	var chart1=AwesomeChart('chartCanvas19');\
	</script>\
        </div>\
	</body>\
	</html>')
}
