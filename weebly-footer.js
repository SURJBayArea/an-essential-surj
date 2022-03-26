<script>
var parent = $( "#wsite-content" )[0];

var events = parent.children;

var array = Array.from(events);

function date2Int(year, month, day) {
 return 10000 * +year + 100 * +month + +day;
};

function extractDate2Int(el) {
  try {
    var date_string = el.querySelector("div.blog-header").querySelector("p.blog-date").querySelector('span.date-text').innerHTML.replace(/\s/g,'')
    var split =  date_string.split('/')
    return date2Int(split[2], split[0], split[1]);
  } catch(e) {
    return -1;
  }
};

if (location.pathname.endsWith('events') || location.pathname.endsWith('intro-to-surj') || location.pathname.endsWith('meeting')) {
  array.sort(function(a, b) {
    var a_date = extractDate2Int(a);
    var b_date = extractDate2Int(b);
    return a_date == b_date
            ? 0
            : (a_date > b_date ? -1 : 1);
  });

  var today = new Date()
  year = today.getFullYear()
  month = 1 + today.getMonth()
  day = today.getDate()
  todayInt = date2Int(year, month, day);

  for (var ii = 0; ii < array.length; ii++) {
    var old = parent.removeChild(array[ii])
    if (extractDate2Int(old) >= todayInt) {
      parent.prepend(old)
    };
  };
}
</script>