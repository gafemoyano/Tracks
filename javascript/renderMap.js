 var map, pointarray, heatmap;
 var points = [];


 function handleFileSelect(evt) {
     var files = evt.target.files; // FileList object
     var reader = new FileReader();
     var output = [];
     reader.onload = function (event) {
         var contents = event.target.result;
         var lines = contents.split('\n');
       
         for (var i = 1, length = lines.length; i < length; i++) {
             var info = lines[i].split(',');
             var lat = info[0];
             var lon = info[1];
             var w = parseInt(info[2]);
             var p = new google.maps.LatLng(lat, lon);
             var weightedLoc = {
                 location: p,
                 weight: w,
             };
             points.push(weightedLoc);
         }
        
     };
     // Read in the image file as a binary string.
     reader.readAsText(evt.target.files[0]);
 }

 function initialize() {
     var mapOptions = {
         zoom: 13,
         center: new google.maps.LatLng(41.8737582915, -87.6860737712),
         mapTypeId: google.maps.MapTypeId.ROADMAP
     };

     map = new google.maps.Map(document.getElementById('map_canvas'),
     mapOptions);

 }

 function toggleHeatmap() {
     var pointArray = new google.maps.MVCArray(points);
     heatmap = new google.maps.visualization.HeatmapLayer({
         data: pointArray
     });

     heatmap.setMap(map);
     heatmap.setOptions({radius: heatmap.get('radius') ? null : 15});
     heatmap.setOptions({opacity: heatmap.get('opacity') ? null : 1.0});
     heatmap.setOptions({maxIntensity: heatmap.get('maxIntensity')? null : 0.8})
     
 }

 google.maps.event.addDomListener(window, 'load', initialize);
 document.getElementById('files').addEventListener('change', handleFileSelect, false);