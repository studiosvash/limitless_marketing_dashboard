# OnPage API Documentation
*Consolidated main text documentation of OnPage API compiled from docs.dataforseo.com*

---


### Overview
*Source: [https://docs.dataforseo.com/v3/on_page/overview/](https://docs.dataforseo.com/v3/on_page/overview/)*
### OnPage API: Overview

OnPage API is the customizable crawling engine for extracting website performance data

#### Endpoints and Parameters

OnPage API encompasses multiple endpoints, which allow you to crawl any website or webpage according to customizable parameters and evaluate its on-page optimization performance against a multitude of SEO and website health benchmarks.

Sending a website for crawling is done through a POST request to the [OnPage Task Post](https://docs.dataforseo.com/v3/on_page/task_post/) endpoint. Alongside the required input fields (domain name or URL and maximum number of pages to crawl), you can also use additional customizable parameters, such as:

**● Custom thresholds** are applied through the `checks_threshold` field in the Task Post request and can be used to customize default threshold values for parameters in the `checks` array of OnPage API responses.

**● Custom JavaScript rules** are applied through the `custom_js` field in the Task Post request and can be used to execute a custom JavaScript code when crawling pages. You can also use the `enable_javascript` parameter to execute built-in JavaScript rules set on a crawled site.

**● Store raw HTML** is applied through the `store_raw_html` field in the Task Post request and can be used to obtain the HTML of the crawled page by making a request to the [Raw HTML](https://docs.dataforseo.com/v3/on_page/raw_html) endpoint.

Besides these parameters, you can also instruct our crawler to:

**● `load_resources`** such as images, stylesheets, scripts, and broken resources;

**● `enable_javascript`** – that is execute Javascript on the crawled pages;

**● `enable_browser_rendering`** to measure Core Web Vitals;

**● `calculate_keyword_density`** to obtain keyword density values for target site.

**Note:** additional charges may apply. To learn more about the cost of all OnPage API parameters, please refer to [this help article](https://dataforseo.com/help-center/cost-of-onpage-api-parameters). Check our [Pricing](https://dataforseo.com/pricing/on-page) to calculate the costs.

After the website is fetched for crawling, you can start retrieving results using the following endpoints:

- [Summary](https://docs.dataforseo.com/v3/on_page/summary/) – provides a summary of on-page issues found on a website;
- [Pages](https://docs.dataforseo.com/v3/on_page/pages/) – returns a list of crawled pages with check-ups and other page performance metrics;
- [Pages by Resource](https://docs.dataforseo.com/v3/on_page/page_by_resource/) – provides a list of pages and related data that contain a specific resource;
- [Resources](https://docs.dataforseo.com/v3/on_page/resources/) – offers a list of resources on a website, including images, scripts, stylesheets, etc.;
- [Duplicate Tags](https://docs.dataforseo.com/v3/on_page/duplicate_tags/) – returns a list of pages that contain duplicate title or description tags;
- [Duplicate Content](https://docs.dataforseo.com/v3/on_page/duplicate_content/) – returns a list of pages that have content similar to the page specified in the request;

- [Links](https://docs.dataforseo.com/v3/on_page/links/) – provides a list of internal and external links detected on a target website;
- [Redirect Chains](https://docs.dataforseo.com/v3/on_page/redirect_chains/) – helps to quickly identify and trace down multiple redirects issues;
- [Non-indexable](https://docs.dataforseo.com/v3/on_page/non_indexable/) – returns a list of pages that are blocked from being indexed by search engines;
- [Waterfall](https://docs.dataforseo.com/v3/on_page/waterfall/)– provides page speed insights data;
- [Keyword Density](https://docs.dataforseo.com/v3/on_page/keyword_density/) – provides keyword density and keyword frequency data for terms appearing on the specified website or web page;
- [Raw HTML](https://docs.dataforseo.com/v3/on_page/raw_html/) – returns the HTML of a page you indicate in the request.

You can fetch data on pages gradually as our crawler processes the pages; this way you don’t have to wait until all the submitted pages are crawled. Alternatively, you can request complete results when the crawling is finished. The crawling process indicator is the `crawl_progress` field in the results of the [Summary](https://docs.dataforseo.com/v3/on_page/summary/) endpoint.

OnPage API allows you to use pingbacks by specifying the `pingback_url` when setting a task, and we will notify you upon the completion of tasks. Learn more on our [Help Center.](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) If you use the Standard method without specifying the `pingback_url`, you can receive the list of id for all completed tasks using the **‘Tasks Ready’** endpoint. It is designed to provide you with a list of completed tasks, which haven’t been collected yet.

Besides auditing sites with the endpoints listed above, you can also perform quick scans of individual pages with the [Instant Pages](https://docs.dataforseo.com/v3/on_page/instant_pages) endpoint and capture screenshots of individual pages using the [Page Screenshot](https://docs.dataforseo.com/v3/on_page/page_screenshot) endpoint. Both of these endpoint work in the Live mode, meaning that you’ll get the results right away in the API response without making a separate request.

To find answers on common questions about OnPage API and find guidance on efficient use of its features, [visit our Help Center.](https://dataforseo.com/help-center/category/onpage-api)

#### Limits and Force Stop

Using the [Task POST](https://docs.dataforseo.com/v3/on_page/task_post/?bash) function, you can send up to 2000 API calls per minute, with each POST call containing no more than 100 tasks. Contact us if you’d like to raise the limit.

**Note 1:** For all other endpoints of OnPage API (except Instant Pages and Page Screenshot), we do not recommend sending several tasks in one POST call as it may result in system overload and undesirable 4xx or 5xx errors.

**Note 2:** Unlike other OnPage API endpoints, [Instant Pages](https://docs.dataforseo.com/v3/on_page/instant_pages) and [Page Screenshot](https://docs.dataforseo.com/v3/on_page/page_screenshot) work based on a Live method of data processing, meaning you don’t have to make a separate GET request to obtain the results. Using this endpoint, you can send up to 2000 API requests per minute, with each request containing no more than 20 tasks.

**Note 3:** The maximum number of simultaneous requests you can send is limited to 30.

In case you need to force stop the crawl process of websites you specified in a task, use [the Force Stop endpoint](https://docs.dataforseo.com/v3/on_page/force_stop/?bash).

Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-onpage-api-requests) to get practical tips for request handling depending on your OnPage API payload volume.

##### The crawling requests will be sent from the following IPs:

`94.130.93.30
168.119.141.170
168.119.99.190
168.119.99.191
168.119.99.192
168.119.99.193
168.119.99.194
68.183.60.34
134.209.42.109
68.183.60.80
68.183.54.131
68.183.49.222
68.183.149.30
68.183.157.22
68.183.149.129`

##### The default user agent of the DataForSEO OnPage Crawler

`Mozilla/5.0 (compatible; RSiteAuditor)`

Note that the user agent can be customized by the user.

#### Cost

The cost of using OnPage API endpoints depends on the parameters set in the [OnPage Task Post](https://docs.dataforseo.com/v3/on_page/task_post/) request. In particular, using `load_resources`, `enable_javascript`, `enable_browser_rendering`, and `calculate_keyword_density` parameters will result in additional charges. To learn more about the cost of all OnPage API parameters, please refer to [this help article](https://dataforseo.com/help-center/cost-of-onpage-api-parameters).

Your account is charged for the actual number of crawled pages. If you specified more pages than a website contains, the difference will be refunded to your account after a task is completed.

The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page) page. You can check your spending in your [account dashboard](https://app.dataforseo.com/api-access) or by making a separate call to [the User Data endpoint.](https://docs.dataforseo.com/v3/appendix/user_data/?php)

You can test OnPage API for free using DataForSEO [Sandbox.](https://docs.dataforseo.com/v3/appendix/sandbox/)

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

---


### Filters and Thresholds
*Source: [https://docs.dataforseo.com/v3/on_page/filters_and_thresholds/](https://docs.dataforseo.com/v3/on_page/filters_and_thresholds/)*
#### Filters and customizable thresholds at DataForSEO OnPage API

OnPage API supports plenty of customizable crawling parameters that allow you to adapt the extraction of website data to your requirements and modify the thresholds for various performance indicators.

Here you will find all the necessary information about filters and thresholds that can be used with DataForSEO OnPage API endpoints.

Note that filters and thresholds are associated with a certain object in the `result` array, and thus should be specified accordingly.

• [Filters](#filters)
• [Thresholds](#thresholds)

#### []()Filters

You will receive the full list of filters by calling this API. Download the full list of possible filters [by this link.](https://cdn.dataforseo.com/v3/available_filters.php?api=on_page)
You can learn more about how to use filters in [this help center article](https://dataforseo.com/help-center/using-filters).

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/on_page/available_filters

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | array | *contains the parameters passed in the URL of the GET request* |
| **`result`** | array | *array of results*<br>contains the full list of available parameters that can be used for data filtration<br>the parameters are grouped by the endpoint they can be used with |

Below you will find a detailed description of `filters` available in OnPage API endpoints. You can specify up to 8 filters by using the `and`, `or` logical operators between the conditions.

The table provides a list of parameters that can be used for data filtration in a certain endpoint, a well as operators supported with each parameter, and other relevant data.

The following operators are supported in OnPage API: `regex`, `not_regex`, `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`, `like`, `not_like`, `match`, `not_match`.
The `regex` and `not_regex` operators can be specified with string values using the [RE2 regex](https://github.com/google/re2/wiki/Syntax) syntax;
**Note:** the maximum limit for the number of characters you can specify in `regex` and `not_regex` is **1000**;
Use the `%` operator with `like` and `not_like` to match any string of zero or more characters.
You can also filter the results by fields provided in the `array` by applying the `has` or `has_not`operator to a filter field.

Example:
`[["fetch_timing.duration_time",">",1],"and",[["total_transfer_size",">",100],"or",["checks.high_loading_time","=",true]],"and",["meta.duplicate_meta_tags","has","generator"]]`

**Description of the available filters:**

`checks.is_http`bool*page with the http protocol*
the following operators are supported: `=`, `<>`
example:
`"filters": ["checks.is_http","<>","false"]``checks.is_http`bool*page with the http protocol*
the following operators are supported: `=`, `<>`
example:
`"filters": ["checks.is_http","<>","false"]`

| Field name | Type | Description |
| --- | --- | --- |
| **filters available for the [resources](https://docs.dataforseo.com/v3/on_page/resources/?php) endpoint:** | | |
| `resource_type` | str | *type of the returned resource*<br>possible types: `script`, `image`, `stylesheet`, `broken`<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`, `match`, `not_match`<br>example:<br>`"filters": [["resource_type","like","image"],"and",["checks.is_broken","=","true"]]` |
| `meta.alternative_text` | str | *content of the image alt atribute*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": [["meta.alternative_text","=","logo"],"or",["meta.alternative_text","like","%trademark%"]]` |
| `meta.title` | str | *content of title atribute*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": [["meta.title","=","how to cook cake"],"or",["meta.title","like","%cake%"]]` |
| `meta.original_width` | num | *original image width in pixels*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": [["meta.original_width","in", [800,1024]],"and",["meta.original_height","in",[600,768]]]` |
| `meta.original_height` | num | *original image height in pixels*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": [["meta.original_width","<", "320"]],"and",["meta.original_height","<","240"]]` |
| `meta.width` | num | *image width in pixels*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": [["meta.width","in", [800,1024]],"and",["meta.height","in",[600,768]]]` |
| `meta.height` | num | *image height in pixels*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": [["meta.width","<", "320"]],"and",["meta.height","<","240"]]` |
| `status_code` | num | *status code of the page where a given resource is located*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["status_code","<>", "200"]` |
| `location` | num | *status code of the page where a given resource is located*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["status_code","<>", "200"]` |
| `url` | str | *resource URL*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": [url","like","%shop%"]` |
| `size` | num | *resource size*<br>indicates the size of a given resource measured in bytes<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["size",">", "47000"]` |
| `encoded_size` | num | *resource size after encoding*<br>indicates the size of the encoded resource measured in bytes<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in``"filters": ["size",">", "11000"]` |
| `total_transfer_size` | num | *compressed resource size*<br>indicates the compressed size of a given resource in bytes<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["size",">", "11000"]` |
| `fetch_time` | time | *date and time when a resource was fetched*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["fetch_time",">","2021-01-29 01:24:54"]` |
| `fetch_timing.duration_time` | num | *indicates how many milliseconds it took to fetch a resource*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["fetch_timing.duration_time",">","50"]<br>` |
| `fetch_timing.fetch_start` | num | *the amount of milliseconds a browser needs to start downloading a resource*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["fetch_timing.fetch_start",">","20"]` |
| `fetch_timing.fetch_end` | num | *the amount of millisends the browser needs to complete downloading a resource*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["fetch_timing.fetch_end",">","50"]` |
| `cache_control.cachable` | bool | *indicates whether the resource is cacheable*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["cache_control.cachable","=","false"]` |
| `cache_control.ttl` | num | *time to live*<br>the amount of time it takes for the browser to cache a resource; measured in milliseconds<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["cache_control.ttl",">","5"]` |
| `checks.no_content_encoding` | bool | *resource with no content encoding*<br>indicates whether a page has no [compression algorithm](http://www.iana.org/assignments/http-parameters/http-parameters.xhtml#content-coding) of the content<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.no_content_encoding","=","true"]` |
| `checks.high_loading_time` | bool | *resource with high loading time*<br>indicates whether a resource loading time exceeds 3 seconds<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.high_loading_time","=","true"]` |
| `checks.is_redirect` | bool | *resource with redirects*<br>indicates whether a page with a resource has `3XX` redirects to other pages<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.is_redirect","=","true"]` |
| `checks.is_4xx_code` | bool | *resource with `4xx` status codes*<br>indicates whether a resource has `4xx` response code<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.is_4xx_code","=","true"]` |
| `checks.is_5xx_code` | bool | *resource with `5xx` status codes*<br>indicates whether a resource has `5xx` response code<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.is_5xx_code","=","true"]` |
| `checks.is_broken` | bool | *broken resource*<br>indicates whether a page with this resource returns a `404` response code<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.is_broken","=","false"]` |
| `checks.is_www` | bool | *page with www*<br>indicates whether a page with this resource is on a `www` subdomain<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.is_www","<>","true"]` |
| `checks.is_https` | bool | *page with the https protocol*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.is_https","<>","false"]` |
| `checks.is_http` | bool | *page with the http protocol*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.is_http","<>","false"]` |
| `checks.is_minified` | bool | *resource is minified*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.is_minified","<>","false"]` |
| `checks.has_redirect` | bool | *resource has a redirect*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.has_redirect","<>","false"]` |
| `checks.from_sitemap` | bool | *resource contains subrequests*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.from_sitemap","=","true"]` |
| `checks.has_subrequests` | bool | *resource contains subrequests*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.has_subrequests","<>","false"]` |
| `content_encoding` | str | *type of encoding*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": ["content_encoding","<>","gzip"]` |
| `media_type` | str | *types of media used to display a resource*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters":["media_type","like","%javascript"]` |
| `accept_type` | str | *indicates the expected type of resource*<br>for example, if `"resource_type": "broken"`, `accept_type` will indicate the type of the broken resource<br>possible values:<br>`any`, `none`, `image`, `sitemap`, `robots`, `script`, `stylesheet`, `redirect`, `html`, `text`, `other`, `font`<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters":["accept_type","like","script"]` |
| `server` | str | *server version*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters":["server","not_like","Amazon%"]` |
| **filters available for the [pages](https://docs.dataforseo.com/v3/on_page/pages/?php) endpoint:** | | |
| `resource_type` | str | *type of the returned page*<br>possible types: `html`, `broken`, `redirect`<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": ["resource_type","=","html"]` |
| `meta.title` | str | *page title*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": [["meta.title","like","%updates%"],"or",["meta.title","like","%news%"]]` |
| `meta.charset` | num | *[code page](https://en.wikipedia.org/wiki/Code_page)*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.charset","in","65000,65001"]` |
| `meta.follow` | bool | *indicates whether a page is indexable*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["meta.follow","=","true"]` |
| `meta.generator` | str | *meta tag generator*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": [["meta.generator","like","%Powered by%"]],"or",["meta.generator","like","%WordPress%"]]` |
| `meta.description` | str | *content of the `description` meta tag*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": ["meta.description","like","%Powered by%"]` |
| `meta.favicon` | str | *image height in pixels*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": ["meta.favicon","like","%cropped-Favicon_512-32x32.png"]` |
| `meta.meta_keywords` | str | *content of the `keywords` meta tag*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": ["meta.meta_keywords","<>","null"]` |
| `meta.canonical` | str | *canonical page*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": ["meta.canonical","like","https://dataforseo.com/apis%"]` |
| `meta.internal_links_count` | num | *number of internal links on the page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.internal_links_count",">=","10"]` |
| `meta.external_links_count` | num | *number of external links on the page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.external_links_count",">=","5"]` |
| `meta.inbound_links_count` | num | *number of internal links pointing at the page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.inbound_links_count",">=","5"]` |
| `meta.images_count` | num | *number of images on the page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.images_count",">=","1"]` |
| `meta.images_size` | num | *total size of images on the page measured in bytes*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.images_size","<=","1000"]` |
| `meta.scripts_count` | num | *number of scripts on the page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.scripts_count",">=","2"]` |
| `meta.scripts_size` | num | *total size of scripts on the page measured in bytes*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.scripts_size",">=","1000"]` |
| `meta.stylesheets_count` | num | *number of stylesheets on the page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.stylesheets_count",">=","1"]` |
| `meta.stylesheets_size` | num | *total size of stylesheets on the page measured in bytes*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.stylesheets_size",">=","1000"]` |
| `meta.title_length` | num | *length of the `title` tag in characters*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.title_length",">=","60"]` |
| `meta.description_length` | num | *length of the `description` tag in characters*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.description_length",">=","120"]` |
| `meta.render_blocking_scripts_count` | num | *number of scripts on the page that block page rendering*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.render_blocking_scripts_count",">=","1"]` |
| `meta.render_blocking_stylesheets_count` | num | *number of CSS styles on the page that block page rendering*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.render_blocking_stylesheets_count",">=","1"]` |
| `meta.cumulative_layout_shift` | num | *Core Web Vitals metric measuring the layout stability of a page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.cumulative_layout_shift",">=","0.25"]` |
| `meta.content.plain_text_size` | num | *total size of the text on the page measured in bytes*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.content.plain_text_size","<=","5000"]` |
| `meta.content.plain_text_rate` | num | *plain text rate value*<br>`plain_text_size` to `size` ratio<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.content.plain_text_rate",">","0.03"]` |
| `meta.content.plain_text_word_count` | num | *number of words on the page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.content.plain_text_word_count",">=","500"]` |
| `meta.content.automated_readability_index` | num | *[Automated Readability Index](https://en.wikipedia.org/wiki/Automated_readability_index)*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.content.automated_readability_index","<=","10"]` |
| `meta.content.coleman_liau_readability_index` | num | *[Coleman–Liau Index](https://en.wikipedia.org/wiki/Coleman%E2%80%93Liau_index)*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.content.coleman_liau_readability_index","<=","10"]` |
| `meta.content.dale_chall_readability_index` | num | *[Dale–Chall Readability Index](https://en.wikipedia.org/wiki/Dale%E2%80%93Chall_readability_formula)*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.content.dale_chall_readability_index","<=","10"]` |
| `meta.content.flesch_kincaid_readability_index` | num | *[Flesch–Kincaid Readability Index](https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests)*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.content.flesch_kincaid_readability_index","<=","10"]` |
| `meta.content.smog_readability_index` | num | *[SMOG Readability Index](https://en.wikipedia.org/wiki/SMOG)*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.content.smog_readability_index","<=","10"]` |
| `meta.content.description_to_content_consistency` | num | *consistency of the meta `description` tag with the page content*<br>measured from 0 to 1<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.content.description_to_content_consistency","<=","0.5"]` |
| `meta.content.title_to_content_consistency` | num | *consistency of the meta `title` tag with the page content*<br>measured from 0 to 1<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.content.title_to_content_consistency","<=","0.7"]` |
| `meta.content.meta_keywords_to_content_consistency` | num | *consistency of meta `keywords`tag with the page content*<br>measured from 0 to 1<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.content.meta_keywords_to_content_consistency","<>","0"]` |
| `meta.spell` | str | *spellcheck*<br>spellcheck errors and suggestions<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": ["meta.spell","<>","null"]` |
| `meta.duplicate_meta_tags` | array.str | *duplicate meta tags*<br>the following operators are supported: `has`<br>example:<br>`"filters": ["meta.duplicate_meta_tags","has","generator"]` |
| `page_timing.time_to_interactive` | num | *[Time To Interactive (TTI)](https://web.dev/interactive/) metric*<br>the time it takes until the user can interact with a page (in milliseconds)<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_timing.time_to_interactive",">=","50"]` |
| `page_timing.dom_complete` | num | *time to load resources*<br>the time it takes until the page and all of its subresources are downloaded (in milliseconds)<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_timing.dom_complete",">=","50"]` |
| `page_timing.largest_contentful_paint` | num | *Core Web Vitals metric measuring how fast the largest above-the-fold content element is displayed*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_timing.largest_contentful_paint",">=","2600"]` |
| `page_timing.first_input_delay` | num | *Core Web Vitals metric indicating the responsiveness of a page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_timing.first_input_delay",">=","0.05"]` |
| `page_timing.connection_time` | num | *time to connect to a server*<br>the time it takes until the connection with a server is established (in milliseconds)<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_timing.connection_time",">=","50"]` |
| `page_timing.time_to_secure_connection` | num | *time to establish a secure connection*<br>the time it takes until the secure connection with a server is established (in milliseconds)<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_timing.time_to_secure_connection",">=","10"]` |
| `page_timing.request_sent_time` | num | *time to send a request to a server*<br>the time it takes until the request to a server is sent (in milliseconds)<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_timing.request_sent_time",">=","5"]` |
| `page_timing.waiting_time` | num | *time to first byte [(TTFB)](https://en.wikipedia.org/wiki/Time_to_first_byte) in milliseconds*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_timing.waiting_time",">=","50"]` |
| `page_timing.download_time` | num | *time it takes for a browser to receive a response (in milliseconds)*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_timing.download_time",">=","20"]` |
| `page_timing.duration_time` | num | *total time it takes until a browser receives a complete response from a server (in milliseconds)*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_timing.duration_time",">=","40"]` |
| `page_timing.fetch_start` | num | *time to start downloading the HTML resource*<br>the amount of time the browser needs to start downloading a page<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_timing.fetch_start",">=","50"]` |
| `page_timing.fetch_end` | num | *time to complete downloading the HTML resource*<br>the amount of time the browser needs to complete downloading a page<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_timing.fetch_end",">=","100"]` |
| `onpage_score` | num | *shows how page is optimized on a 100-point scale*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["onpage_score",">=","50"]` |
| `total_dom_size` | num | *total [DOM](https://developers.google.com/web/tools/chrome-devtools/dom) size of a page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["total_dom_size",">=","200000"]` |
| `broken_resources` | bool | *indicates whether a page contains broken resources*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["broken_resources","=","true"]` |
| `broken_links` | bool | *indicates whether a page contains broken links*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["broken_links","<>","false"]` |
| `duplicate_title` | bool | *indicates whether a page has duplicate `title` tags*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["duplicate_title","=","false"]` |
| `duplicate_description` | bool | *indicates whether a page has a duplicate description*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["duplicate_description","<>","true"]` |
| `duplicate_content` | bool | *indicates whether a page has duplicate content*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["duplicate_content","=","true"]` |
| `status_code` | num | *status code of the page where a given resource is located*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["status_code","<>", "200"]` |
| `location` | num | *status code of the page where a given resource is located*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["status_code","<>", "200"]` |
| `url` | str | *resource URL*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": [url","like","%shop%"]` |
| `click_depth` | num | *number of clicks it takes to get to the page*<br>indicates the number of clicks from the homepage needed before landing at the target page<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["click_depth",">", "4"]` |
| `size` | num | *resource size*<br>indicates the size of a given resource measured in bytes<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["size",">", "47000"]` |
| `encoded_size` | num | *resource size after encoding*<br>indicates the size of the encoded resource measured in bytes<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["encoded_size",">", "11000"]` |
| `total_transfer_size` | num | *compressed resource size*<br>indicates the compressed size of a given resource in bytes<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["total_transfer_size",">", "11000"]` |
| `fetch_time` | time | *date and time when a resource was fetched*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["fetch_time",">","2021-01-29 01:24:54"]` |
| `cache_control.cachable` | bool | *indicates whether the resource is cacheable*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["cache_control.cachable","=","false"]` |
| `cache_control.ttl` | num | *time to live*<br>the amount of time it takes for the browser to cache a resource; measured in milliseconds<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["cache_control.ttl",">","5"]` |
| `checks.no_content_encoding` | bool | *resource with no content encoding*<br>indicates whether a page has no [compression algorithm](http://www.iana.org/assignments/http-parameters/http-parameters.xhtml#content-coding) of the content<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.no_content_encoding","=","true"]` |
| `checks.high_loading_time` | bool | *resource with high loading time*<br>indicates whether a resource loading time exceeds 3 seconds<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.high_loading_time","=","true"]` |
| `checks.is_redirect` | bool | *resource with redirects*<br>indicates whether a page with a resource has `3XX` redirects to other pages<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.is_redirect","=","true"]` |
| `checks.is_4xx_code` | bool | *page with `4xx` status codes*<br>indicates whether a page has `4xx` response code<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.is_4xx_code","=","true"]` |
| `checks.is_5xx_code` | bool | *page with `5xx` status codes*<br>indicates whether a page has `5xx` response code<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.is_5xx_code","=","true"]` |
| `checks.is_broken` | bool | *broken resource*<br>indicates whether a page with this resource returns a `404` response code<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.is_broken","=","false"]` |
| `checks.is_www` | bool | *page with www*<br>indicates whether a page with this resource is on a `www` subdomain<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.is_www","<>","true"]` |
| `checks.is_https` | bool | *page with the https protocol*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.is_https","<>","false"]` |
| `checks.high_waiting_time` | bool | *page with high waiting time*<br>indicates whether a page waiting time (aka Time to First Byte) exceeds 1.5 seconds<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.high_waiting_time","=","true"]` |
| `checks.has_micromarkup` | bool | *page has [microdata markup](https://en.wikipedia.org/wiki/Microdata_(HTML))*<br>indicates whether a page returns microdata markup<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.has_micromarkup","=","true"]` |
| `checks.has_micromarkup_errors` | bool | *page microdata markup returns errors*<br>indicates whether the microdata markup of a page returns an error<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.has_micromarkup_errors","=","true"]` |
| `checks.no_doctype` | bool | *page with no doctype*<br>indicates whether a page is without the `<!DOCTYPE HTML>` declaration<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.no_doctype","=","true"]` |
| `checks.canonical` | bool | *page is canonical*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.canonical","=","false"]` |
| `checks.no_encoding_meta_tag` | bool | *page with no meta tag encoding*<br>indicates whether a page is without `Content-Type`<br>informative only if the encoding is not explicit in the `Content-Type` header<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.no_encoding_meta_tag","=","true"]` |
| `checks.no_h1_tags` | bool | *page with empty or absent h1 tags*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.no_h1_tags","=","true"]` |
| `checks.https_to_http_links` | bool | *HTTPS page has links to HTTP pages*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.https_to_http_links","=","true"]` |
| `checks.has_html_doctype` | bool | *page with HTML doctype declaration*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.has_html_doctype","=","false"]` |
| `checks.size_greater_than_3mb` | bool | *page with size larger than 3 MB*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.size_greater_than_3mb","=","true"]` |
| `checks.meta_charset_consistency` | bool | *page with meta charset tag*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.meta_charset_consistency","=","true"]` |
| `checks.has_meta_refresh_redirect` | bool | *pages with meta refresh redirect*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.has_meta_refresh_redirect","=","true"]` |
| `checks.has_render_blocking_resources` | bool | *page with render-blocking resources*<br>if `true`, the page has render-blocking scripts or stylesheets<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.has_render_blocking_resources","=","true"]` |
| `checks.redirect_chain` | bool | *page with multiple redirects*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.redirect_chain","=","true"]` |
| `checks.recursive_canonical` | bool | *recursive canonical error*<br>`true` if the page contains `rel="canonical"` tag to another page, which in turn, refers back to the initial page<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.recursive_canonical","=","true"]` |
| `checks.low_content_rate` | bool | *page with low content rate*<br>indicates whether a page has the `plain_text size` to `page size` ratio of less than 0.1<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.low_content_rate","=","true"]` |
| `checks.high_content_rate` | bool | *page with high content rate*<br>indicates whether a page has the `plain_text size` to `page size` ratio of more than 0.9<br>available for canonical pages only<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.high_content_rate","=","true"]` |
| `checks.low_character_count` | bool | *indicates whether the page has less than 1024 characters*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.low_character_count","=","true"]` |
| `checks.high_character_count` | bool | *indicates whether the page has more than 256,000 characters*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.high_character_count","=","true"]` |
| `checks.small_page_size` | bool | *indicates whether a page is too small*<br>the value will be `true` if a page size is smaller than 1024 bytes<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.small_page_size","=","true"]` |
| `checks.large_page_size` | bool | *indicates whether a page is too heavy*<br>the value will be `true` if a page size exceeds 1 megabyte<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.large_page_size","=","true"]` |
| `checks.low_readability_rate` | bool | *page with a low readability rate*<br>indicates whether a page is scored less than 15 points on the [Flesch–Kincaid readability test](https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests)<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.low_readability_rate","=","true"]` |
| `checks.irrelevant_description` | bool | *page with irrelevant description*<br>indicates whether a page `description` tag is irrelevant to the content of a page<br>the relevance threshold is `0.2`<br>available for canonical pages only<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.irrelevant_description","=","true"]` |
| `checks.irrelevant_title` | bool | *page with irrelevant title*<br>indicates whether a page `title` tag is irrelevant to the content of the page<br>the relevance threshold is `0.3`<br>available for canonical pages only<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.irrelevant_title","=","true"]` |
| `checks.irrelevant_meta_keywords` | bool | *page with irrelevant meta keywords*<br>indicates whether a page `keywords` tags are irrelevant to the content of a page<br>the relevance threshold is `0.6`<br>available for canonical pages only<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.irrelevant_meta_keywords","=","true"]` |
| `checks.title_too_long` | bool | *page with a long title*<br>indicates whether the content of the `title` tag exceeds 65 characters<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.title_too_long","=","true"]` |
| `checks.title_too_short` | bool | *page with short titles*<br>indicates whether the content of `title` tag is shorter than 30 characters<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.title_too_short","=","true"]` |
| `checks.deprecated_html_tags` | bool | *page with deprecated tags*<br>indicates whether a page has [deprecated HTML tags](https://www.codehelp.co.uk/html/deprecated.html)<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.deprecated_html_tags","=","true"]` |
| `checks.duplicate_meta_tags` | bool | *page with duplicate meta tags*<br>indicates whether a page has more than one meta tag of the same type<br>available for canonical pages only<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.duplicate_meta_tags","=","true"]` |
| `checks.duplicate_title_tag` | bool | *page with more than one title tag*<br>indicates whether a page has more than one `title` tag<br>available for canonical pages only<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.duplicate_title_tag","=","true"]` |
| `checks.no_image_alt` | bool | *images without `alt` tags*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.no_image_alt","=","true"]` |
| `checks.no_image_title` | bool | *images without `title` tags*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.no_image_title","=","true"]` |
| `checks.no_description` | bool | *pages with no description*<br>indicates whether a page has an empty or absent `description` meta tag<br>available for canonical pages only<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.no_description","=","true"]` |
| `checks.no_title` | bool | *page with no title*<br>indicates whether a page has an empty or absent `title` tag<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.no_title","=","true"]` |
| `checks.no_favicon` | bool | *page with no favicon*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.no_favicon","=","true"]` |
| `checks.seo_friendly_url` | bool | *page with seo-frienldy URL*<br>the ‘SEO-friendliness’ of a page URL is checked by four parameters:<br>– the length of the relative path is less than 120 characters<br>– no special characters<br>– no dynamic parameters<br>– relevance of the URL to the page<br>if at least one of them is failed then such URL is considered as not ‘SEO-friendly’<br>the data is available for canonical pages only<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.seo_friendly_url","=","true"]` |
| `checks.flash` | bool | *page with flash*<br>indicates whether a page has flash elements<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.flash","=","true"]` |
| `checks.frame` | bool | *page with frames*<br>indicates whether a page contains `frame`, `iframe`, `frameset` tags<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.frame","=","true"]` |
| `checks.lorem_ipsum` | bool | *page with lorem ipsum*<br>indicates whether a page has *lorem ipsum* content<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.lorem_ipsum","=","true"]` |
| `checks.seo_friendly_url_characters_check` | bool | *URL characters check-up*<br>indicates whether a page URL containing only uppercase and lowercase Latin characters, digits and dashes<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.seo_friendly_url_characters_check","=","false"]` |
| `checks.seo_friendly_url_dynamic_check` | bool | *URL dynamic check-up*<br>the value will be `true` if a page has no dynamic parameters in the URL<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.seo_friendly_url_dynamic_check","=","false"]` |
| `checks.seo_friendly_url_keywords_check` | bool | *URL keyword check-up*<br>indicates whether a page URL is consistent with the `title` meta tag<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.seo_friendly_url_keywords_check","=","false"]` |
| `checks.seo_friendly_url_relative_length_check` | bool | *URL length check-up*<br>the value will be `true` if a page URL no longer than 120 characters<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.seo_friendly_url_relative_length_check","=","false"]` |
| `checks.canonical_chain` | bool | *pages with canonical pointing to a page that has a canonical pointing elsewhere*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.canonical_chain","=","true"]` |
| `checks.canonical_to_redirect` | bool | *canonical page pointing to a page that redirects elsewhere*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.canonical_to_redirect","=","true"]` |
| `checks.canonical_to_broken` | bool | *canonical link pointing to a broken page*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.canonical_to_broken","=","true"]` |
| `checks.has_links_to_redirects` | bool | *page is pointing to a page that redirect elsewhere*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.has_links_to_redirects","=","true"]` |
| `checks.is_orphan_page` | bool | *page with no internal links pointing to it*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.is_orphan_page","=","true"]` |
| `checks.is_link_relation_conflict` | bool | *mix of both followed and nofollowed incoming internal links*<br>`true` if the page receives at least one link with the `rel="nofollow"` attribute and at least one dofollow link<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.is_link_relation_conflict","=","true"]` |
| `checks.from_sitemap` | bool | *resource contains subrequests*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.from_sitemap","=","true"]` |
| `content_encoding` | str | *type of encoding*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": ["content_encoding","<>","gzip"]` |
| `media_type` | str | *types of media used to display a resource*<br>the following operators are supported: `regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters":["media_type","like","%text%"]` |
| `server` | str | *server version*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters":["server","not_like","Amazon%"]` |
| `is_resource` | bool | *whether a page is a resource*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["is_resource","=","false"]` |
| `url_length` | num | *page URL length in characters*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["url_length",">","10"]` |
| `relative_url_length` | num | *relative URL length in characters*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["relative_url_length",">","4"]` |
| **filters available for the [non_indexable](https://docs.dataforseo.com/v3/on_page/non_indexable/?php) endpoint:** | | |
| `reason` | str | *the reason why the page is non-indexable*<br>can take the following values: `robots_txt`, `meta_tag`, `http_header`, `attribute`, `too_many_redirects`<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters":["reason","=","robots_txt"]` |
| `url` | str | *url of the non-indexable page*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters":["url","like","%blog%"]` |
| **filters available for the [links](https://docs.dataforseo.com/v3/on_page/links/?php) endpoint:** | | |
| `type` | str | *type of a link*<br>can take the following values: `anchor`, `image`, `link`, `canonical`, `meta`, `alternate`<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters":[["type","=","anchor"],"or",["type","=","link"]] ` |
| `domain_from` | str | *referring domain*<br>the link was found on this domain<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters":["domain_from","like","%dataforseo.com%"]` |
| `domain_to` | str | *referenced domain*<br>the link is pointing to this domain<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters":["domain_to","like","%dataforseo.com%"]` |
| `page_from` | str | *referring page*<br>relative URL of the page on which the link was found<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters":["page_from","like","dataforseo.com/blog%"]` |
| `page_to` | str | *referenced page*<br>relative URL of the page to which the link is pointing<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters":["page_to","like","app.dataforseo.com%"]` |
| `link_from` | str | *referring page*<br>absolute URL of the page on which the link was found<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters":["link_from","like","%dataforseo.com/blog%"]` |
| `link_to` | str | *referenced page*<br>absolute URL of the page to which the link is pointing<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters":["link_to","like","%app.dataforseo.com%"]` |
| `link_attribute` | array | *link attribute added to external link*<br>absolute URL of the page to which the link is pointing<br>indicates link attributes added to the `link_to` on the `page_from`<br>the following operators are supported: `has`<br>example:<br>`"filters":["link_attribute","has","ugc"]` |
| `dofollow` | bool | *indicates whether the link is dofollow*<br>if the value is `true`, the link doesn’t have a `rel="nofollow"` attribute<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["dofollow","=","true"]` |
| `page_from_scheme` | str | *[url scheme](https://en.wikipedia.org/wiki/List_of_URI_schemes) of the referring page*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters":["page_from_scheme","=","https"]` |
| `page_to_scheme` | str | *[url scheme](https://en.wikipedia.org/wiki/List_of_URI_schemes) of the referenced page*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters":["page_to_scheme","=","nntp"]` |
| `direction` | str | *direction of the link*<br>possible values: `internal`, `external`<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters":["direction","=","internal"]` |
| `page_to_status_code` | num | *status code of the referenced page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters":["page_to_status_code","=", "200"]` |
| **filters available for the [pages by resource](https://docs.dataforseo.com/v3/on_page/page_by_resource/?php) endpoint:** | | |
| `resource_type` | str | *type of the returned page*<br>possible types: `html`, `broken`<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": ["resource_type","=","html"]` |
| `meta.title` | str | *page title*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": [["meta.title","like","%updates%"],"or",["meta.title","like","%news%"]]` |
| `meta.charset` | num | *[code page](https://en.wikipedia.org/wiki/Code_page)*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.charset","in","65000,65001"]` |
| `meta.follow` | bool | *indicates whether a page is indexable*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["meta.follow","=","true"]` |
| `meta.generator` | str | *meta tag generator*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": [["meta.generator","like","%Powered by%"]],"or",["meta.generator","like","%WordPress%"]]` |
| `meta.description` | str | *content of the `description` meta tag*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": ["meta.description","like","%Powered by%"]` |
| `meta.favicon` | str | *image height in pixels*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": ["meta.favicon","like","%cropped-Favicon_512-32x32.png"]` |
| `meta.meta_keywords` | str | *content of the `keywords` meta tag*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": ["meta.meta_keywords","<>","null"]` |
| `meta.canonical` | str | *canonical page*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": ["meta.canonical","like","https://dataforseo.com/apis%"]` |
| `meta.internal_links_count` | num | *number of internal links on the page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.internal_links_count",">=","10"]` |
| `meta.external_links_count` | num | *number of external links on the page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.external_links_count",">=","5"]` |
| `meta.inbound_links_count` | num | *number of internal links pointing at the page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.inbound_links_count",">=","5"]` |
| `meta.images_count` | num | *number of images on the page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.images_count",">=","1"]` |
| `meta.images_size` | num | *total size of images on the page measured in bytes*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.images_size","<=","1000"]` |
| `meta.scripts_count` | num | *number of scripts on the page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.scripts_count",">=","2"]` |
| `meta.scripts_size` | num | *total size of scripts on the page measured in bytes*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.scripts_size",">=","1000"]` |
| `meta.stylesheets_count` | num | *number of stylesheets on the page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.stylesheets_count",">=","1"]` |
| `meta.stylesheets_size` | num | *total size of stylesheets on the page measured in bytes*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.stylesheets_size",">=","1000"]` |
| `meta.title_length` | num | *length of the `title` tag in characters*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.title_length",">=","60"]` |
| `meta.description_length` | num | *length of the `description` tag in characters*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.description_length",">=","120"]` |
| `meta.render_blocking_scripts_count` | num | *number of scripts on the page that block page rendering*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.render_blocking_scripts_count",">=","1"]` |
| `meta.render_blocking_stylesheets_count` | num | *number of CSS styles on the page that block page rendering*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.render_blocking_stylesheets_count",">=","1"]` |
| `meta.cumulative_layout_shift` | num | *Core Web Vitals metric measuring the layout stability of a page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.cumulative_layout_shift",">=","0.25"]` |
| `meta.content.plain_text_size` | num | *total size of the text on the page measured in bytes*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.content.plain_text_size","<=","5000"]` |
| `meta.content.plain_text_rate` | num | *plain text rate value*<br>`plain_text_size` to `size` ratio<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.content.plain_text_rate",">","0.03"]` |
| `meta.content.plain_text_word_count` | num | *number of words on the page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.content.plain_text_word_count",">=","500"]` |
| `meta.content.automated_readability_index` | num | *[Automated Readability Index](https://en.wikipedia.org/wiki/Automated_readability_index)*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.content.automated_readability_index","<=","10"]` |
| `meta.content.coleman_liau_readability_index` | num | *[Coleman–Liau Index](https://en.wikipedia.org/wiki/Coleman%E2%80%93Liau_index)*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.content.coleman_liau_readability_index","<=","10"]` |
| `meta.content.dale_chall_readability_index` | num | *[Dale–Chall Readability Index](https://en.wikipedia.org/wiki/Dale%E2%80%93Chall_readability_formula)*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.content.dale_chall_readability_index","<=","10"]` |
| `meta.content.flesch_kincaid_readability_index` | num | *[Flesch–Kincaid Readability Index](https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests)*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.content.flesch_kincaid_readability_index","<=","10"]` |
| `meta.content.smog_readability_index` | num | *[SMOG Readability Index](https://en.wikipedia.org/wiki/SMOG)*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.content.smog_readability_index","<=","10"]` |
| `meta.content.description_to_content_consistency` | num | *consistency of the meta `description` tag with the page content*<br>measured from 0 to 1<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.content.description_to_content_consistency","<=","0.5"]` |
| `meta.content.title_to_content_consistency` | num | *consistency of the meta `title` tag with the page content*<br>measured from 0 to 1<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.content.title_to_content_consistency","<=","0.7"]` |
| `meta.content.meta_keywords_to_content_consistency` | num | *consistency of meta `keywords`tag with the page content*<br>measured from 0 to 1<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["meta.content.meta_keywords_to_content_consistency","<>","0"]` |
| `meta.spell` | str | *spellcheck*<br>spellcheck errors and suggestions<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": ["meta.spell","<>","null"]` |
| `meta.duplicate_meta_tags` | array.str | *duplicate meta tags*<br>the following operators are supported: `has`<br>example:<br>`"filters": ["meta.duplicate_meta_tags","has","generator"]` |
| `page_timing.time_to_interactive` | num | *[Time To Interactive (TTI)](https://web.dev/interactive/) metric*<br>the time it takes until the user can interact with a page (in milliseconds)<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_timing.time_to_interactive",">=","50"]` |
| `page_timing.dom_complete` | num | *time to load resources*<br>the time it takes until the page and all of its subresources are downloaded (in milliseconds)<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_timing.dom_complete",">=","50"]` |
| `page_timing.largest_contentful_paint` | num | *Core Web Vitals metric measuring how fast the largest above-the-fold content element is displayed*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_timing.largest_contentful_paint",">=","2600"]` |
| `page_timing.first_input_delay` | num | *Core Web Vitals metric indicating the responsiveness of a page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_timing.first_input_delay",">=","0.05"]` |
| `page_timing.connection_time` | num | *time to connect to a server*<br>the time it takes until the connection with a server is established (in milliseconds)<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_timing.connection_time",">=","50"]` |
| `page_timing.time_to_secure_connection` | num | *time to establish a secure connection*<br>the time it takes until the secure connection with a server is established (in milliseconds)<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_timing.time_to_secure_connection",">=","10"]` |
| `page_timing.request_sent_time` | num | *time to send a request to a server*<br>the time it takes until the request to a server is sent (in milliseconds)<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_timing.request_sent_time",">=","5"]` |
| `page_timing.waiting_time` | num | *time to first byte [(TTFB)](https://en.wikipedia.org/wiki/Time_to_first_byte) in milliseconds*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_timing.waiting_time",">=","50"]` |
| `page_timing.download_time` | num | *time it takes for a browser to receive a response (in milliseconds)*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_timing.download_time",">=","20"]` |
| `page_timing.duration_time` | num | *total time it takes until a browser receives a complete response from a server (in milliseconds)*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_timing.duration_time",">=","40"]` |
| `page_timing.fetch_start` | num | *time to start downloading the HTML resource*<br>the amount of time the browser needs to start downloading a page<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_timing.fetch_start",">=","50"]` |
| `page_timing.fetch_end` | num | *time to complete downloading the HTML resource*<br>the amount of time the browser needs to complete downloading a page<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_timing.fetch_end",">=","100"]` |
| `onpage_score` | num | *shows how page is optimized on a 100-point scale*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["onpage_score",">=","50"]` |
| `total_dom_size` | num | *total [DOM](https://developers.google.com/web/tools/chrome-devtools/dom) size of a page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["total_dom_size",">=","200000"]` |
| `broken_resources` | bool | *indicates whether a page contains broken resources*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["broken_resources","=","true"]` |
| `broken_links` | bool | *indicates whether a page contains broken links*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["broken_links","<>","false"]` |
| `duplicate_title` | bool | *indicates whether a page has duplicate `title` tags*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["duplicate_title","=","false"]` |
| `duplicate_description` | bool | *indicates whether a page has a duplicate description*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["duplicate_description","<>","true"]` |
| `duplicate_content` | bool | *indicates whether a page has duplicate content*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["duplicate_content","=","true"]` |
| `status_code` | num | *status code of the page where a given resource is located*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["status_code","<>", "200"]` |
| `location` | num | *status code of the page where a given resource is located*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["status_code","<>", "200"]` |
| `url` | str | *resource URL*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": [url","like","%shop%"]` |
| `size` | num | *resource size*<br>indicates the size of a given resource measured in bytes<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["size",">", "47000"]` |
| `encoded_size` | num | *resource size after encoding*<br>indicates the size of the encoded resource measured in bytes<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["encoded_size",">", "11000"]` |
| `total_transfer_size` | num | *compressed resource size*<br>indicates the compressed size of a given resource in bytes<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["total_transfer_size",">", "11000"]` |
| `fetch_time` | time | *date and time when a resource was fetched*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["fetch_time",">","2021-01-29 01:24:54"]` |
| `cache_control.cachable` | bool | *indicates whether the resource is cacheable*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["cache_control.cachable","=","false"]` |
| `cache_control.ttl` | num | *time to live*<br>the amount of time it takes for the browser to cache a resource; measured in milliseconds<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["cache_control.ttl",">","5"]` |
| `checks.no_content_encoding` | bool | *resource with no content encoding*<br>indicates whether a page has no [compression algorithm](http://www.iana.org/assignments/http-parameters/http-parameters.xhtml#content-coding) of the content<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.no_content_encoding","=","true"]` |
| `checks.high_loading_time` | bool | *resource with high loading time*<br>indicates whether a resource loading time exceeds 3 seconds<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.high_loading_time","=","true"]` |
| `checks.is_redirect` | bool | *resource with redirects*<br>indicates whether a page with a resource has `3XX` redirects to other pages<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.is_redirect","=","true"]` |
| `checks.is_4xx_code` | bool | *page with `4xx` status codes*<br>indicates whether a page has `4xx` response code<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.is_4xx_code","=","true"]` |
| `checks.is_5xx_code` | bool | *page with `5xx` status codes*<br>indicates whether a page has `5xx` response code<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.is_5xx_code","=","true"]` |
| `checks.is_broken` | bool | *broken resource*<br>indicates whether a page with this resource returns a `404` response code<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.is_broken","=","false"]` |
| `checks.is_www` | bool | *page with www*<br>indicates whether a page with this resource is on a `www` subdomain<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.is_www","<>","true"]` |
| `checks.is_https` | bool | *page with the https protocol*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.is_https","<>","false"]` |
| `checks.high_waiting_time` | bool | *page with high waiting time*<br>indicates whether a page waiting time (aka Time to First Byte) exceeds 1.5 seconds<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.high_waiting_time","=","true"]` |
| `checks.no_doctype` | bool | *page with no doctype*<br>indicates whether a page is without the `<!DOCTYPE HTML>` declaration<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.no_doctype","=","true"]` |
| `checks.canonical` | bool | *page is canonical*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.canonical","=","false"]` |
| `checks.no_encoding_meta_tag` | bool | *page with no meta tag encoding*<br>indicates whether a page is without `Content-Type`<br>informative only if the encoding is not explicit in the `Content-Type` header<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.no_encoding_meta_tag","=","true"]` |
| `checks.no_h1_tags` | bool | *page with empty or absent h1 tags*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.no_h1_tags","=","true"]` |
| `checks.https_to_http_links` | bool | *HTTPS page has links to HTTP pages*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.https_to_http_links","=","true"]` |
| `checks.has_html_doctype` | bool | *page with HTML doctype declaration*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.has_html_doctype","=","false"]` |
| `checks.size_greater_than_3mb` | bool | *page with size larger than 3 MB*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.size_greater_than_3mb","=","true"]` |
| `checks.meta_charset_consistency` | bool | *page with meta charset tag*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.meta_charset_consistency","=","true"]` |
| `checks.has_meta_refresh_redirect` | bool | *pages with meta refresh redirect*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.has_meta_refresh_redirect","=","true"]` |
| `checks.has_render_blocking_resources` | bool | *page with render-blocking resources*<br>if `true`, the page has render-blocking scripts or stylesheets<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.has_render_blocking_resources","=","true"]` |
| `checks.redirect_chain` | bool | *page with multiple redirects*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.redirect_chain","=","true"]` |
| `checks.recursive_canonical` | bool | *recursive canonical error*<br>`true` if the page contains `rel="canonical"` tag to another page, which in turn, refers back to the initial page<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.recursive_canonical","=","true"]` |
| `checks.low_content_rate` | bool | *page with low content rate*<br>indicates whether a page has the `plain_text size` to `page size` ratio of less than 0.1<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.low_content_rate","=","true"]` |
| `checks.high_content_rate` | bool | *page with high content rate*<br>indicates whether a page has the `plain_text size` to `page size` ratio of more than 0.9<br>available for canonical pages only<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.high_content_rate","=","true"]` |
| `checks.low_character_count` | bool | *indicates whether the page has less than 1024 characters*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.low_character_count","=","true"]` |
| `checks.high_character_count` | bool | *indicates whether the page has more than 256,000 characters*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.high_character_count","=","true"]` |
| `checks.small_page_size` | bool | *indicates whether a page is too small*<br>the value will be `true` if a page size is smaller than 1024 bytes<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.small_page_size","=","true"]` |
| `checks.large_page_size` | bool | *indicates whether a page is too heavy*<br>the value will be `true` if a page size exceeds 1 megabyte<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.large_page_size","=","true"]` |
| `checks.low_readability_rate` | bool | *page with a low readability rate*<br>indicates whether a page is scored less than 15 points on the [Flesch–Kincaid readability test](https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests)<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.low_readability_rate","=","true"]` |
| `checks.irrelevant_description` | bool | *page with irrelevant description*<br>indicates whether a page `description` tag is irrelevant to the content of a page<br>the relevance threshold is `0.2`<br>available for canonical pages only<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.irrelevant_description","=","true"]` |
| `checks.irrelevant_title` | bool | *page with irrelevant title*<br>indicates whether a page `title` tag is irrelevant to the content of the page<br>the relevance threshold is `0.3`<br>available for canonical pages only<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.irrelevant_title","=","true"]` |
| `checks.irrelevant_meta_keywords` | bool | *page with irrelevant meta keywords*<br>indicates whether a page `keywords` tags are irrelevant to the content of a page<br>the relevance threshold is `0.6`<br>available for canonical pages only<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.irrelevant_meta_keywords","=","true"]` |
| `checks.title_too_long` | bool | *page with a long title*<br>indicates whether the content of the `title` tag exceeds 65 characters<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.title_too_long","=","true"]` |
| `checks.title_too_short` | bool | *page with short titles*<br>indicates whether the content of `title` tag is shorter than 30 characters<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.title_too_short","=","true"]` |
| `checks.deprecated_html_tags` | bool | *page with deprecated tags*<br>indicates whether a page has [deprecated HTML tags](https://www.codehelp.co.uk/html/deprecated.html)<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.deprecated_html_tags","=","true"]` |
| `checks.duplicate_meta_tags` | bool | *page with duplicate meta tags*<br>indicates whether a page has more than one meta tag of the same type<br>available for canonical pages only<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.duplicate_meta_tags","=","true"]` |
| `checks.duplicate_title_tag` | bool | *page with more than one title tag*<br>indicates whether a page has more than one `title` tag<br>available for canonical pages only<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.duplicate_title_tag","=","true"]` |
| `checks.no_image_alt` | bool | *images without `alt` tags*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.no_image_alt","=","true"]` |
| `checks.no_image_title` | bool | *images without `title` tags*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.no_image_title","=","true"]` |
| `checks.no_description` | bool | *pages with no description*<br>indicates whether a page has an empty or absent `description` meta tag<br>available for canonical pages only<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.no_description","=","true"]` |
| `checks.no_title` | bool | *page with no title*<br>indicates whether a page has an empty or absent `title` tag<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.no_title","=","true"]` |
| `checks.no_favicon` | bool | *page with no favicon*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.no_favicon","=","true"]` |
| `checks.seo_friendly_url` | bool | *page with seo-frienldy URL*<br>the ‘SEO-friendliness’ of a page URL is checked by four parameters:<br>– the length of the relative path is less than 120 characters<br>– no special characters<br>– no dynamic parameters<br>– relevance of the URL to the page<br>if at least one of them is failed then such URL is considered as not ‘SEO-friendly’<br>the data is available for canonical pages only<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.seo_friendly_url","=","true"]` |
| `checks.flash` | bool | *page with flash*<br>indicates whether a page has flash elements<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.flash","=","true"]` |
| `checks.frame` | bool | *page with frames*<br>indicates whether a page contains `frame`, `iframe`, `frameset` tags<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.frame","=","true"]` |
| `checks.lorem_ipsum` | bool | *page with lorem ipsum*<br>indicates whether a page has *lorem ipsum* content<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.lorem_ipsum","=","true"]` |
| `checks.seo_friendly_url_characters_check` | bool | *URL characters check-up*<br>indicates whether a page URL containing only uppercase and lowercase Latin characters, digits and dashes<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.seo_friendly_url_characters_check","=","false"]` |
| `checks.seo_friendly_url_dynamic_check` | bool | *URL dynamic check-up*<br>the value will be `true` if a page has no dynamic parameters in the URL<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.seo_friendly_url_dynamic_check","=","false"]` |
| `checks.seo_friendly_url_keywords_check` | bool | *URL keyword check-up*<br>indicates whether a page URL is consistent with the `title` meta tag<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.seo_friendly_url_keywords_check","=","false"]` |
| `checks.seo_friendly_url_relative_length_check` | bool | *URL length check-up*<br>the value will be `true` if a page URL no longer than 120 characters<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.seo_friendly_url_relative_length_check","=","false"]` |
| `checks.canonical_chain` | bool | *pages with canonical pointing to a page that has a canonical pointing elsewhere*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.canonical_chain","=","true"]` |
| `checks.canonical_to_redirect` | bool | *canonical page pointing to a page that redirects elsewhere*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.canonical_to_redirect","=","true"]` |
| `checks.canonical_to_broken` | bool | *canonical link pointing to a broken page*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.canonical_to_broken","=","true"]` |
| `checks.has_links_to_redirects` | bool | *page is pointing to a page that redirect elsewhere*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.has_links_to_redirects","=","true"]` |
| `checks.is_orphan_page` | bool | *page with no internal links pointing to it*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.is_orphan_page","=","true"]` |
| `checks.is_link_relation_conflict` | bool | *mix of both followed and nofollowed incoming internal links*<br>`true` if the page receives at least one link with the `rel="nofollow"` attribute and at least one dofollow link<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.is_link_relation_conflict","=","true"]` |
| `checks.from_sitemap` | bool | *resource contains subrequests*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["checks.from_sitemap","=","true"]` |
| `content_encoding` | str | *type of encoding*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": ["content_encoding","<>","gzip"]` |
| `media_type` | str | *types of media used to display a resource*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters":["media_type","like","%text%"]` |
| `server` | str | *server version*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters":["server","not_like","Amazon%"]` |
| `server` | str | *server version*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters":["server","not_like","Amazon%"]` |
| `is_resource` | bool | *whether a page is a resource*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["is_resource","=","false"]` |
| **filters available for the [keyword density](https://docs.dataforseo.com/v3/on_page/keyword_density/?bash) endpoint:** | | |
| `keyword` | str | *keyword found on the website of web page*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters":["keyword","not_like","seo%"]` |
| `frequency` | num | *keyword frequency*<br>number of times the keyword appears on the website (or webpage if you specified a `url` when setting a task to [the keyword density endpoint](https://docs.dataforseo.com/v3/on_page/keyword_density/?bash))<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["frequency",">","6"]` |
| `density` | num | *keyword density*<br>ratio of `frequency` to the total count of keywords with the set `keyword_length` on the web page or website<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["density",">","0.02"]` |
| **filters available for the [uncrawlable resources](https://docs.dataforseo.com/v3/on_page/uncrawlable_resources/) endpoint:** | | |
| `url` | str | *URL of the uncrawlable resource*<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": [“url","like","%shop%"]` |
| `reason` | str | *reason the resource is uncrawlable*<br>can take the following values: `content_type_inconsistency`<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": [“reason","=","content_type_inconsistency"]` |
| `status_code` | num | *HTTP response code returned by the uncrawlable resource*<br>can take the following values: `200`<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["status_code","=","200"]` |
| `fetch_time` | time | *date and time when the resource was fetched*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["fetch_time",">","2026-04-29 01:24:54"]` |
| `meta.content_type` | str | *actual content type of the resource*<br>can take the following values: `content_type_inconsistency`<br>the following operators are supported: `regex`, `not_regex`, `=`, `<>`, `like`, `not_like`,`match`, `not_match`<br>example:<br>`"filters": [“meta.content_type","=","image/jpeg"]` |

#### []()Thresholds

Below you will find a detailed description of OnPage API fields, which you can customize through the `checks_threshold` array of the [POST request to OnPage API](https://docs.dataforseo.com/v3/on_page/task_post/)

**Description of the customizable checks thresholds:**

| Field name | Type | Description |
| --- | --- | --- |
| `title_too_short` | integer | *page title is too short*<br>specified as the number of characters in the title tag of the page<br>if the number of characters is less than or equals the specified value, the pages matching the set criteria will be flagged in the API response<br>default value: `30`<br>example:<br>`"checks_threshold": {<br>"title_too_short": 10}` |
| `title_too_long` | integer | *page title is too long*<br>specified as the number of characters in the title tag of the page<br>if the number of characters is more than or equals the specified value, the pages matching the set criteria will be flagged in the API response<br>default value: `65`<br>example:<br>`"checks_threshold": {<br>"title_too_long": 50}` |
| `small_page_size` | integer | *page is too small*<br>specified as the weight of the page measured in bytes<br>if the page weight is less than or equals the specified value, the pages matching the set criteria will be flagged in the API response<br>default value: `1024`<br>example:<br>`"checks_threshold": {<br>"small_page_size": 2048}` |
| `large_page_size` | integer | *page is too large*<br>specified as the weight of the page measured in bytes<br>if the page weight is more than or equals the specified value, the pages matching the set criteria will be flagged in the API response<br>default value: `1048576` (or 1024*1024)<br>example:<br>`"checks_threshold": {<br>"large_page_size": 2000000}` |
| `low_character_count` | integer | *character count is too low*<br>specified as the number of characters on the page<br>if the number of characters on the page is less than or equals the specified value, the pages matching the set criteria will be flagged in the API response<br>default value: `1024` (or 1024*1024)<br>example:<br>`"checks_threshold": {<br>"low_character_count": 2000000}` |
| `high_character_count` | integer | *character count is too high*<br>specified as the number of characters on the page<br>if the number of characters on the page is more than or equals the specified value, the pages matching the set criteria will be flagged in the API response<br>default value: `256000` (or 250*1024)<br>example:<br>`"checks_threshold": {<br>"high_character_count": 500000}` |
| `low_content_rate` | float | *content rate is too low*<br>specified as the `plain_text_size` to `page_size` ratio<br>if the number of characters on the page is less than or equals the specified value, the pages matching the set criteria will be flagged in the API response<br>default value: `0.1`<br>example:<br>`"checks_threshold": {<br>"low_content_rate": 0.3}` |
| `high_content_rate` | float | *content rate is too high*<br>specified as the `plain_text_size` to `page_size` ratio<br>if the number of characters on the page is more than or equals the specified value, the pages matching the set criteria will be flagged in the API response<br>default value: `0.9`<br>example:<br>`"checks_threshold": {<br>"high_content_rate": 0.8}` |
| `high_loading_time` | integer | *page loading time is too high*<br>specified as the number of milliseconds it takes a page to fully load<br>if the loading time is more than or equals the specified value, the pages matching the set criteria will be flagged in the API response<br>default value: `3000`<br>example:<br>`"checks_threshold": {<br>"high_loading_time": 4000}` |
| `high_waiting_time` | integer | *page waiting time is too high*<br>specified as the Time to First Byte in milliseconds<br>if the waiting time is more than or equals the specified value, the pages matching the set criteria will be flagged in the API response<br>default value: `1500`<br>example:<br>`"checks_threshold": {<br>"high_waiting_time": 1000}` |
| `low_readability_rate` | integer | *page readability rate is too high*<br>specified as the [Flesch–Kincaid readability test](https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests) score<br>if the score is more than or equals the specified value, the pages matching the set criteria will be flagged in the API response<br>default value: `15.0`<br>example:<br>`"checks_threshold": {<br>"low_readability_rate": 20.5}` |
| `irrelevant_description` | float | *page description is not relevant to its content*<br>specified as the match rate of page’s description to its content<br>if the score is less than or equals the specified value, the pages matching the set criteria will be flagged in the API response<br>default value: `0.2`<br>example:<br>`"checks_threshold": {<br>"irrelevant_description": 0.5}` |
| `irrelevant_title` | integer | *page title is not relevant to its content*<br>specified as the match rate of page’s title to its content<br>if the score is less than or equals the specified value, the pages matching the set criteria will be flagged in the API response<br>default value: `0.3`<br>example:<br>`"checks_threshold": {<br>"irrelevant_title": 0.1}` |
| `irrelevant_meta_keywords` | integer | *page meta keywords are not relevant to its content*<br>specified as the match rate of page’s meta keywords to its content<br>if the score is less than or equals the specified value, the pages matching the set criteria will be flagged in the API response<br>default value: `0.6`<br>example:<br>`"checks_threshold": {<br>"irrelevant_meta_keywords": 0.5}` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The list of available filtration parameters:

---


### Force Stop
*Source: [https://docs.dataforseo.com/v3/on_page/force_stop/](https://docs.dataforseo.com/v3/on_page/force_stop/)*
#### OnPage API Force Stop

This endpoint is designed to force stop the crawl process of websites you specified in a task. The execution of all the tasks associated with the IDs indicated in your request to this endpoint will be stopped. You will still be able to obtain the data on pages that have been scanned until the crawling process was stopped.

POSThttps://api.dataforseo.com/v3/on_page/force_stop

Pricing

Your account will not be charged for using this function. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page/onpage-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *ID of the task*<br>**required field**<br>you can get this ID in the response of the [Task POST](https://docs.dataforseo.com/v3/on_page/task_post/) endpoint<br>example:<br>“07131248-1535-0216-1000-17384017ad04”<br>**note**: you can set up to 1000 `id` values as separate objects in the POST array |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| ** `result`** | array | *array of results* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Task POST
*Source: [https://docs.dataforseo.com/v3/on_page/task_post/](https://docs.dataforseo.com/v3/on_page/task_post/)*
#### Setting OnPage Tasks

OnPage API checks websites for 60+ customizable on-page parameters defines and displays all found flaws and opportunities for optimization so that you can easily fix them. It checks meta tags, duplicate content, image tags, response codes, and other parameters on every page. You can find the full list of OnPage API check-up parameters in the [Pages](https://docs.dataforseo.com/v3/on_page/pages) section.

POSThttps://api.dataforseo.com/v3/on_page/task_post

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page/onpage-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). Task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, with each POST call containing no more than 100 tasks. If your POST call contains over 100 tasks, the tasks over this limit will return the `40006` error.
The maximum number of simultaneous requests you can send is limited to 30.

Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-onpage-api-requests) to get practical tips for request handling depending on your OnPage API payload volume.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `target` | string | *target domain*<br>**required field**<br>domain name should be specified without `https://` and `www.`<br>if you specify the page URL, the results will be returned for the domain included in the URL |
| `max_crawl_pages` | integer | *crawled pages limit*<br>**required field**<br>the number of pages to crawl on the specified domain<br>**Note:**<br>if you set `max_crawl_pages` to 1 and do not specify `start_url` or set a homepage in it, the following sitewide checks will be disabled:<br>`test_canonicalization`, `enable_www_redirect_check`, `test_hidden_server_signature`, `test_page_not_found`, `test_directory_browsing`, `test_https_redirect`<br>to enable them anyway, set `force_sitewide_checks` to `true`if you set `max_crawl_pages` to 1 and specify `start_url` other than a homepage, all sitewide checks will be disabled;<br>to enable them anyway, set `force_sitewide_checks` to `true` |
| `start_url` | string | *the first url to crawl *<br>optional field<br>**Note:** you should specify an absolute URL<br>if you want to crawl a single page, specify its URL in this field and additionally set the `max_crawl_pages` parameter to `1`<br>you can also use the [live Instant Pages endpoint](https://docs.dataforseo.com/v3/on_page/instant_pages/?bash) to get page-specific data |
| `force_sitewide_checks` | boolean | *enable sitewide checks when crawling a single page*<br>optional field<br>set to `true` to get data on sitewide checks when crawling a single page;<br>default value: `false` |
| `priority_urls` | array | *urls to be crawled bypassing the queue*<br>optional field<br>URLs specified in this array will be crawled in the first instance, bypassing the crawling queue;<br>**Note:** you should specify the absolute URL;<br>you can specify up to **20 URLs**;<br>all URLs in the array must belong to the `target` domain;<br>subdomains will be ignored unless the `allow_subdomains` parameter is set to `true`example:<br>`"priority_urls": [<br>"https://dataforseo.com/apis/serp-api",<br>"https://dataforseo.com/contact"<br>]` |
| `max_crawl_depth` | integer | *crawl depth*<br>optional field<br>the linking depth of the pages to crawl;<br>for example, starting page of the crawl is level 0, pages that have links from that page are level 1, etc. |
| `crawl_delay` | integer | *delay between hits, ms*<br>optional field<br>the custom delay between crawler hits to the server<br>default value: `2000` |
| `store_raw_html` | boolean | *store HTML of crawled pages*<br>optional field<br>set to `true` if you want to get the HTML of the page using the [OnPage Raw HTML endpoint](https://docs.dataforseo.com/v3/on_page/raw_html/)<br>default value: `false` |
| `enable_content_parsing` | boolean | *parse content on crawled pages*<br>optional field<br>set to `true` to use the [OnPage Content Parsing endpoint](https://docs.dataforseo.com/v3/on_page/content_parsing/live/)<br>default value: `false` |
| `support_cookies` | boolean | *support cookies on crawled pages*<br>optional field<br>set to `true` to support cookies when crawling the pages<br>default value: `false` |
| `accept_language` | string | *language header for accessing the website*<br>optional field<br>all locale formats are supported (xx, xx-XX, xxx-XX, etc.)<br>**Note:** if you do not specify this parameter, some websites may deny access; in this case, pages will be returned with the `"type":"broken` in the response array |
| `custom_robots_txt` | string | *custom robots.txt settings*<br>optional field<br>example: `Disallow: /directory1/` |
| `robots_txt_merge_mode` | string | *merge with or override robots.txt settings*<br>optional field<br>possible values: `merge`, `override`;<br>set to `override` if you want to ignore website crawling restrictions and other robots.txt settings<br>default value: `merge`;<br>**Note:** if set to `override`, specify the `custom_robots_txt` parameter |
| `custom_user_agent` | string | *custom user agent*<br>optional field<br>custom user agent for crawling a website<br>example: `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36<br>`<br>default value: `Mozilla/5.0 (compatible; RSiteAuditor)` |
| `browser_preset` | string | *preset for browser screen parameters*<br>optional field<br>if you use this field, you don’t need to indicate `browser_screen_width`, `browser_screen_height`, `browser_screen_scale_factor`possible values:<br>`desktop`, `mobile`, `tablet``desktop` preset will apply the following values:`browser_screen_width: 1920`<br>`browser_screen_height: 1080`<br>`browser_screen_scale_factor: 1``mobile` preset will apply the following values:`browser_screen_width: 390`<br>`browser_screen_height: 844`<br>`browser_screen_scale_factor: 3``tablet` preset will apply the following values:`browser_screen_width: 1024`<br>`browser_screen_height: 1366`<br>`browser_screen_scale_factor: 2`<br>**Note:** to use this parameter, set `enable_javascript` or `enable_browser_rendering` to `true` |
| `browser_screen_width` | integer | *browser screen width*<br>optional field<br>you can set a custom browser screen width to perform audit for a particular device;<br>if you use this field, you don’t need to indicate `browser_preset` as it will be ignored;<br>**Note:** to use this parameter, set `enable_javascript` or `enable_browser_rendering` to `true`minimum value, in pixels: `240`<br>maximum value, in pixels: `9999` |
| `browser_screen_height` | integer | *browser screen height*<br>optional field<br>you can set a custom browser screen height to perform an audit for a particular device;<br>if you use this field, you don’t need to indicate `browser_preset` as it will be ignored;<br>**Note:** to use this parameter, set `enable_javascript` or `enable_browser_rendering` to `true`minimum value, in pixels: `240`<br>maximum value, in pixels: `9999` |
| `browser_screen_scale_factor` | float | *browser screen scale factor*<br>optional field<br>you can set a custom browser screen resolution ratio to perform audit for a particular device;<br>if you use this field, you don’t need to indicate `browser_preset` as it will be ignored;<br>**Note:** to use this parameter, set `enable_javascript` or `enable_browser_rendering` to `true`minimum value: `0.5`<br>maximum value: `3` |
| `respect_sitemap` | boolean | *respect sitemap when crawling*<br>optional field<br>set to `true` if you want to follow the order of pages indicated in the primary sitemap when crawling;<br>default value: `false`<br>**Note:** if set to `true`, the `click_depth` value in the API response will equal `0`;<br>the `max_crawl_depth` field of the request will be ignored, you can specify the number of pages to crawl using the `max_crawl_pages` parameter<br> |
| `custom_sitemap` | string | *custom sitemap url*<br>optional field<br>the URL of the page where the alternative sitemap is located<br>**Note:** if you want to use this parameter, `respect_sitemap` should be `true` |
| `crawl_sitemap_only` | boolean | *crawl only pages indicated in the sitemap*<br>optional field<br>set to `true` if you want to crawl only the pages indicated in the sitemap<br>if you set this parameter to `true` and do not specify `custom_sitemap`, we will crawl the default sitemap<br>default value: `false`<br>**Note:** if you want to use this parameter, `respect_sitemap` should be `true` |
| `load_resources` | boolean | *load resources*<br>optional field<br>set to `true` if you want to load image, stylesheets, scripts, and broken resources<br>default value: `false`<br>**Note:** if you use this parameter, additional charges will apply; learn more about the cost of tasks with this parameter [in our help article](https://dataforseo.com/help-center/cost-of-onpage-api-parameters); the cost can be calculated on the [Pricing Page](https://dataforseo.com/pricing/on-page/onpage-api) |
| `enable_www_redirect_check` | boolean | *check if the domain implemented the www redirection*<br>optional field<br>set to `true` if you want to check if the requested domain implemented the www to non-www or non-www to www redirect;<br>default value: `false` |
| `enable_javascript` | boolean | *load javascript on a page*<br>optional field<br>set to `true` if you want to load the scripts available on a page<br>default value: `false`<br>**Note:** if you use this parameter, additional charges will apply; learn more about the cost of tasks with this parameter [in our help article](https://dataforseo.com/help-center/cost-of-onpage-api-parameters); the cost can be calculated on the [Pricing Page](https://dataforseo.com/pricing/on-page/onpage-api) |
| `enable_xhr` | boolean | *enable XMLHttpRequest on a page*<br>optional field<br>set to `true` if you want our crawler to request data from a web server using the XMLHttpRequest object<br>default value: `false`;if you use this field, `enable_javascript` must be set to `true`; |
| `enable_browser_rendering` | boolean | *emulate browser rendering to measure Core Web Vitals*<br>optional field<br>by using this parameter you will be able to emulate a browser when loading a web page;<br>`enable_browser_rendering` loads styles, images, fonts, animations, videos, and other resources on a page;<br>default value: `false`<br>set to `true` to obtain Core Web Vitals (FID, CLS, LCP) metrics in the response;<br>**if you use this field, `enable_javascript`, and `load_resources` parameters must be set to `true`**<br>**Note:** if you use this parameter, additional charges will apply; learn more about the cost of tasks with this parameter [in our help article](https://dataforseo.com/help-center/cost-of-onpage-api-parameters); the cost can be calculated on the [Pricing Page](https://dataforseo.com/pricing/on-page/onpage-api) |
| `disable_cookie_popup` | boolean | *disable the cookie popup*<br>optional field<br>set to `true` if you want to disable the popup requesting cookie consent from the user;<br>default value:<br>`false` |
| `custom_js` | string | *custom javascript*<br>optional field<br>**Note** that the execution time for the script you enter here should be 700 ms maximum, for example, you can use the following JS snippet to check if the website contains Google Tag Manager as a `scr` attribute:<br>`let meta = { haveGoogleAnalytics: false, haveTagManager: false };\r\nfor (var i = 0; i < document.scripts.length; i++) {\r\n let src = document.scripts[i].getAttribute(\"src\");\r\n if (src != undefined) {\r\n if (src.indexOf(\"analytics.js\") >= 0)\r\n meta.haveGoogleAnalytics = true;\r\n\tif (src.indexOf(\"gtm.js\") >= 0)\r\n meta.haveTagManager = true;\r\n }\r\n}\r\nmeta;`the returned value depends on what you specified in this field. For instance, if you specify the following script:<br>`meta = {}; meta.url = document.URL; meta.test = 'test'; meta;`<br>as a response you will receive the following data:<br>`"custom_js_response": {<br>"url": "https://dataforseo.com/",<br>"test": "test"<br>}`<br>**Note:** the length of the script you enter must be no more than 2000 characters<br> |
| `validate_micromarkup` | boolean | *enable microdata validation*<br>optional field<br>set to `true` if you want to use the [OnPage API Microdata endpoint](https://docs.dataforseo.com/v3/on_page/microdata/)<br>default value: `false` |
| `allow_subdomains` | boolean | *include pages on subdomains*<br>optional field<br>set to `true` if you want to crawl all subdomains of a target website<br>default value: `false` |
| `allowed_subdomains` | array | *subdomains to crawl*<br>optional field<br>specify subdomains that you want to crawl<br>example: `["blog.site.com", "my.site.com", "shop.site.com"]`<br>**Note:** to use this parameter, the `allow_subdomains` parameter should be set to `false`;<br>otherwise, the content of `allowed_subdomains` field will be ignored and the results will be returned for all subdomains |
| `disallowed_subdomains` | array | *subdomains not to crawl*<br>optional field<br>specify subdomains that you don’t want to crawl<br>example: `["status.site.com", "docs.site.com"]`<br>**Note:** to use this parameter, the `allow_subdomains` parameter should be set to `true` |
| `check_spell` | boolean | *check spelling*<br>optional field<br>set to `true` to check spelling on a website using [Hunspell](http://hunspell.github.io/) library<br>default value: `false` |
| `check_spell_language` | string | *language of the spell check*<br>optional field<br>supported languages: ‘hy’, ‘eu’, ‘bg’, ‘ca’, ‘hr’, ‘cs’, ‘da’, ‘nl’, ‘en’, ‘eo’, ‘et’, ‘fo’, ‘fa’, ‘fr’, ‘fy’, ‘gl’, ‘ka’, ‘de’, ‘el’, ‘he’, ‘hu’, ‘is’, ‘ia’, ‘ga’, ‘it’, ‘rw’, ‘la’, ‘lv’, ‘lt’, ‘mk’, ‘mn’, ‘ne’, ‘nb’, ‘nn’, ‘pl’, ‘pt’, ‘ro’, ‘gd’, ‘sr’, ‘sk’, ‘sl’, ‘es’, ‘sv’, ‘tr’, ‘tk’, ‘uk’, ‘vi’<br>**Note:** if no language is specified, it will be set automatically based on page content |
| `check_spell_exceptions` | array | *words excluded from spell check*<br>optional field<br>specify the words that you want to exclude from spell check<br>maximum word length: 100 characters<br>maximum amount of words: 1000<br>example: `"SERP", "minifiers", "JavaScript"` |
| `calculate_keyword_density` | boolean | *calculate keyword density for the target domain*<br>optional field<br>set to `true` if you want to calculate keyword density for website pages<br>default value: `false`<br>**Note:** if you use this parameter, additional charges will apply; learn more about the cost of tasks with this parameter [in our help article](https://dataforseo.com/help-center/cost-of-onpage-api-parameters)<br>once the crawl is completed, you can obtain keyword density values with [the Keyword Density endpoint](https://docs.dataforseo.com/v3/on_page/keyword_density?bash) |
| `checks_threshold` | object | *custom threshold values for checks*<br>optional field<br>you can specify custom threshold values for the parameters included in the `checks` object of OnPage API responses;<br>**Note:** only integer threshold values can be modified;<br>for example, the `high_loading_time` and `large_page_size` parameters are set to 3 seconds and 1 megabyte respectively by default;<br>if you want to change these thresholds to 1 second and 1000 kbytes, use the following snippet:<br>`"checks_threshold": {<br>"high_loading_time": 1,<br>"large_page_size": 1000<br>}`available customizable parameters with default values:<br>`"title_too_short", default value: 30, type: "int"<br>"title_too_long", default value: 65, type: "int"<br>"small_page_size", default value: 1024, type: "int"<br>"large_page_size", default value: 1048576 (1024 * 1024), type: "int"<br>"low_character_count", default value: 1024, type: "int"<br>"high_character_count", default value: 256000 (250 * 1024), type: "int"<br>"low_content_rate", default value: 0.1, type: "float"<br>"high_content_rate", default value: 0.9, type: "float"<br>"high_loading_time", default value: 3000, type: "int"<br>"high_waiting_time", default value: 1500, type: "int"<br>"low_readability_rate", default value: 15.0, type: "float"<br>"irrelevant_description", default value: 0.2, type: "float"<br>"irrelevant_title", default value: 0.3, type: "float"<br>"irrelevant_meta_keywords", default value: 0.6, type: "float"` |
| `disable_sitewide_checks` | array | *prevent certain sitewide checks from running*<br>optional field<br>specify the following `checks` to prevent them from running on the `target` website:<br>`"test_page_not_found"`<br>`"test_canonicalization"`<br>`"test_https_redirect"`<br>`"test_directory_browsing"`example:<br>`"disable_sitewide_checks": ["test_directory_browsing", "test_page_not_found"]`learn more on [our help center](https://dataforseo.com/help-center/how-to-disable-sitewide-checks-in-onpage-api) |
| `disable_page_checks` | array | *prevent certain page checks from running*<br>optional field<br>specify certain `checks` to prevent them from running and impacting the `onpage_score`example:<br>`"disable_page_checks": ["is_5xx_code", "is_4xx_code"]` |
| `switch_pool` | boolean | *switch proxy pool*<br>optional field<br>if `true`, additional proxy pools will be used to obtain the requested data;<br>the parameter can be used if a multitude of tasks is set simultaneously, resulting in occasional `rate-limit` and/or `site_unreachable` errors |
| `return_despite_timeout` | boolean | *return data on pages despite the timeout error*<br>optional field<br>if `true`, the data will be provided on pages that failed to load within 120 seconds and responded with a timeout error;<br>default value: `false` |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |
| `pingback_url` | string | *notification URL of a completed task*<br>optional field<br>when a task is completed we will notify you by GET request sent to the URL you have specified<br>you can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request.<br>example:<br>`http://your-server.com/pingscript?id=$id`<br>`http://your-server.com/pingscript?id=$id&tag=$tag`<br>**Note:** special characters in `pingback_url` will be urlencoded;<br>i.a., the `#` character will be encoded into `%23`<br>learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results*<br>in this case, the value will be `null` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Tasks Ready
*Source: [https://docs.dataforseo.com/v3/on_page/tasks_ready/](https://docs.dataforseo.com/v3/on_page/tasks_ready/)*
#### On-Page Tasks Ready

The ‘Tasks Ready’ endpoint is designed to provide you with a list of completed tasks, which results haven’t been collected yet.

GEThttps://api.dataforseo.com/v3/on_page/tasks_ready

Pricing

Your account is not charged when receiving results

Each separate task will remain on the list until it is collected. You can make **up to 20 API calls per minute.** With each API call, you can get 1000 tasks completed within three previous days. The list will not contain the tasks which have already been collected and the tasks that were not collected **within three days** after completion.

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | array | *contains the parameters passed in the request’s URL* |
| ** `result`** | array | *array of results* |
| `id` | string | *task identifier of the completed task*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `target` | string | *target website specified when setting a task* |
| `date_posted` | string | *date when the task was posted (in the UTC format)* |
| `tag` | string | *user-defined task identifier* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Summary
*Source: [https://docs.dataforseo.com/v3/on_page/summary/](https://docs.dataforseo.com/v3/on_page/summary/)*
#### OnPage API Summary

Using this function, you can get the overall information on a website as well as drill down into exact on-page issues of a website that has been scanned. As a result, you will know what functions to use for receiving detailed data for each of the found issues.

GEThttps://api.dataforseo.com/v3/on_page/summary/$id

Pricing

Your account will be charged only for posting a task.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page/onpage-api) page.

**Description of the fields for sending a request:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *task identifier*<br>**required field**<br>you can get this ID in the response of the [Task POST](https://docs.dataforseo.com/v3/on_page/task_post/) endpoint<br>example:<br>“07131248-1535-0216-1000-17384017ad04” |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| ** `result`** | array | *array of results* |
| `crawl_progress` | string | *status of the crawling session*<br>possible values: `in_progress`, `finished` |
| `crawl_status` | object | *details of the crawling session* |
| `max_crawl_pages` | integer | *maximum number of pages to crawl*<br>indicates the `max_crawl_pages` limit you specified when setting a task |
| `pages_in_queue` | integer | *number of pages that are currently in the crawling queue* |
| `pages_crawled` | integer | *number of crawled pages* |
| `crawl_gateway_address` | string | *crawler ip address*<br>displays the IP address used by the crawler to initiate the current crawling session<br>you can find the full list of IPs used by our crawler in the [Overview section](https://docs.dataforseo.com/v3/on_page/overview) |
| `crawl_stop_reason` | string | *reason why the crawling stopped*<br>information about the reason why the crawling process stopped;<br>possible values:<br>`limit_exceeded` – the limit set in the `max_crawl_pages` was exceeded;<br>`empty_queue` – all URLs in the queue were crawled;<br>`force_stopped` – the crawling process was halted using the[ On Page API Force Stop](https://docs.dataforseo.com/v3/on_page/force_stop) function;<br>`unexpected_exception` – an internal error was encountered while crawling the `target`, contact support for more info |
| **`domain_info`** | object | *domain-wide info*<br>on-page information about the target domain and crawling process |
| `name` | string | *domain name* |
| `cms` | string | *content management system*<br>content management system identified on a website<br>the content of the `generator` meta tag<br>the data is taken from the first random page that returns the 200 response code<br>if our crawler was unable to identify the cms, the value would be `null` |
| `ip` | string | *domain ip address* |
| `server` | string | *website server*<br>the version of the server detected on a website<br>the content of the `server` header<br>the information is taken from the first page which response code is 200 |
| `crawl_start` | string | *time when the crawling start*<br>date and time when the website was sent for crawling<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `crawl_end` | string | *time when the crawling ended*<br>date and time when the crawling was finished<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>**Note:** informative only if `"crawl_progress"` is `"finished"`<br>if `"crawl_progress"` is `in_progress`, the value will be `null` |
| `extended_crawl_status` | string | *crawl status and errors*<br>indicates the reason why a website was not crawled;<br>can take the following values:<br>`no_errors` – no crawling errors were detected;<br>`site_unreachable` – our crawler could not reach a website and thus was not able to obtain a status code;<br>`invalid_page_status_code` – status code of the first crawled page >= 400;<br>`forbidden_meta_tag` – the first crawled page contains the <meta robots=”noindex”> tag;<br>`forbidden_robots` – robots.txt forbids crawling the page;<br>`forbidden_http_header` – HTTP header of the page contains “X-Robots-Tag: noindex” ;<br>`too_many_redirects` – the first crawled page has more than 10 redirects;<br>`unknown` – the reason is unknown |
| `ssl_info` | object | *ssl certificate info*<br>information about the Secure Sockets Layer protocol detected on a website |
| `valid_certificate` | boolean | *ssl certificate validity*<br>indicates whether the ssl certificate detected on a website is not expired, suspended, revoked or invalid |
| `certificate_issuer` | string | *ssl certificate authority*<br>the entity that issued the detected ssl certificate |
| `certificate_subject` | string | *ssl certificate subject*<br>the entity associated with the public key |
| `certificate_version` | string | *ssl certificate version*<br>indicates the version of [X.509](https://en.wikipedia.org/wiki/X.509) used by an ssl certificate |
| `certificate_hash` | string | *ssl certificate hash*<br>the version of the ssl certificate’s hash function |
| `certificate_expiration_date` | string | *ssl certificate expiration date*<br>the date and time when the ssl certificate expires<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `checks` | object | *website checks*<br>other on-page check-ups related to the website |
| `sitemap` | boolean | *website sitemap*<br>indicates whether a sitemap was detected on a target website |
| `robots_txt` | boolean | *robots.txt file*<br>indicates whether a target website has a robots.txt file |
| `start_page_deny_flag` | boolean | *deny flag on a start page*<br>indicates whether a start page on a target website has a `[F]` flag which causes the server to return a 403 Forbidden status code to the client |
| `ssl` | boolean | *ssl certificate*<br>indicates whether a target website has an SSL certificate |
| `http2` | boolean | *HTTP/2 protocol*<br>indicates whether a target website is using the HTTP/2 protocol |
| `test_canonicalization` | boolean | *canonical tags*<br>the checkup of the server behavior when our crawler tries to access the website via IP;<br>is `true` if the `canonicalization_status_code` returns `301` |
| `test_www_redirect` | boolean | *www to non-www redirect*<br>is `true` if the www to non-www or non-www to www redirect is implemented by the requested domain |
| `test_hidden_server_signature` | boolean | *hidden server signature*<br>indicates whether the server signature is hidden from crawlers<br>if the value is `false`, our crawler was able to access the website’s server signature |
| `test_page_not_found` | boolean | *404 status for a page that cannot be found*<br>indicates whether a target responds with a 404 status code when the requested resource cannot be found |
| `test_directory_browsing` | boolean | *directory browsing not accessible*<br>indicates whether a target website doesn’t allow accessing a file directory without authentication<br>if the directory is not accessible, the value is `true` |
| `test_https_redirect` | boolean | *http requests are redirected to https*<br>indicates whether a target website redirects http requests to the https version;<br>if the website’s home page redirects http requests to https, the value is `true` |
| `total_pages` | integer | *total crawled pages*<br>the total number of crawled pages |
| `total_uncrawlable_resources` | integer | *total uncrawlable resources*<br>the total number of resources that could not be crawled;<br>the resource is considered uncrawlable when the actual content type of the resource doesn’t match the content type expected by the crawler |
| `page_not_found_status_code` | integer | *status code returned by a non-existent page*<br>in most cases, it is recommended a server returns a 404 response code |
| `canonicalization_status_code` | integer | *status code returned by a canonicalized page*<br>the checkup of the server behavior when our crawler tries to access the website via IP;<br>in most cases, it is recommended that canonicalized pages respond with a `301` or `302` status code |
| `directory_browsing_status_code` | integer | *status code returned by a directory*<br>the status code returned by a directory page on a target website<br>in most cases, it is recommended that directories respond with a `403` or `401` status code |
| `www_redirect_status_code` | integer | *redirect status code*<br>the status code of the www to non-www redirect<br>in most cases, it is recommended that redirect returns a `301` status code |
| `main_domain` | string | *root domain name* |
| **`page_metrics`** | object | *page-specific info*<br>metrics information on the target website pages |
| `links_external` | integer | *number of external links*<br>the number of links pointing to other websites |
| `links_internal` | integer | *number of internal links*<br>the number of links pointing to other pages within the target website |
| `duplicate_title` | integer | *number of pages with duplicate titles* |
| `duplicate_description` | integer | *number of pages with duplicate descriptions* |
| `duplicate_content` | integer | *number of pages with duplicate content* |
| `broken_links` | integer | *number of broken links*<br>number of broken links across all crawled pages on a target website |
| `broken_resources` | integer | *number of broken resources*<br>the number of images and other resources with broken links |
| `links_relation_conflict` | integer | *number of links present on the target website that may have a conflict*<br>for example, if `"links_relation_conflict": 2`, the target website is referring to the same source by at least one internal link with the `rel="nofollow"` attribute **and** by at least one dofollow link |
| `redirect_loop` | integer | *number of redirect chains that start and end at the same URL*<br>number of redirect chains where the destination URL redirects back to the original URL |
| `onpage_score` | float | *shows how website is optimized on a 100-point scale*<br>this field shows how website is optimized considering critical on-page issues and warnings detected;<br>`100` is the highest possible score that means website does not have any critical on-page issues and important warnings;<br>**note** that this value depends on the number of crawled pages;<br>learn more about how the metric is calculated in [this help center article](https://dataforseo.com/help-center/how-is-onpage-score-of-a-domain-calculated) |
| `non_indexable` | integer | *number of non-indexable pages*<br>number of pages that are blocked from being indexed by Google and other search engines by robots.txt, HTTP headers, or meta tags settings;<br>you can receive a list of non-indexable URLs using [this endpoint](https://docs.dataforseo.com/v3/on_page/non_indexable/?bash) |
| `checks` | object | *page-specific on-page check-ups* |
| `canonical` | integer | *number of canonical pages* |
| `duplicate_meta_tags` | integer | *number of pages with duplicate meta tags*<br>the number of pages with more than one meta tag of the same type;<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_description` | integer | *number of pages with no description*<br>the number of pages with an empty or absent `description` meta tag;<br>**Note:** available for pages with `canonical` check set to `true` |
| `frame` | integer | *number of pages with frames*<br>the number of pages that contain `frame`, `iframe`, `frameset` tags |
| `large_page_size` | integer | *number of heavy pages*<br>the number of pages that have a size exceeding 1 megabyte;<br>**Note:** available for pages with `canonical` check set to `true` |
| `irrelevant_description` | integer | *number of pages with irrelevant description*<br>the number of pages with `description` tags that are irrelevant to the content of a page;<br>the relevance threshold is `0.2`;<br>**Note:** available for pages with `canonical` check set to `true` |
| `irrelevant_meta_keywords` | integer | *number of pages with irrelevant meta keywords*<br>the number of pages with `keywords` tags that are irrelevant to the content of a page;<br>the relevance threshold is `0.6`;<br>**Note:** available for pages with `canonical` check set to `true` |
| `is_https` | integer | *number of pages with the https protocol* |
| `is_http` | integer | *number of pages with the http protocol* |
| `title_too_long` | integer | *number of pages with long titles*<br>the number of pages with the content of `title` tag exceeding 65 characters;<br>**Note:** available for pages with `canonical` check set to `true` |
| `low_content_rate` | integer | *number of pages with a low content rate*<br>number of pages, which have the `plaintext size` to `page size` ratio of less than 0.1 or more than 0.9;<br>**Note:** available for pages with `canonical` check set to `true` |
| `small_page_size` | integer | *number of small pages*<br>the number of pages that have the size smaller than 1024 bytes;<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_h1_tag` | integer | *number of pages with empty or absent h1 tags*<br>**Note:** available for pages with `canonical` check set to `true` |
| `recursive_canonical` | integer | *recursive canonical error*<br>indicates the number of pages that contain `rel="canonical"` tag to another page, which in turn, refers back to the initial page |
| `no_favicon` | integer | *number of pages with no favicon*<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_image_alt` | integer | *number of pages containing images without `alt` tags*<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_image_title` | integer | *number of pages containing images without `title` tags*<br>**Note:** available for pages with `canonical` check set to `true` |
| `seo_friendly_url` | integer | *number of pages with seo-frienldy urls*<br>the ‘SEO-friendliness’ of a page URL is checked by four parameters:<br>– the length of the relative path is less than 120 characters<br>– no special characters<br>– no dynamic parameters<br>– relevance of the URL to the page<br>if at least one of them is failed then such URL is considered as not ‘SEO-friendly’<br>**Note:** available for pages with `canonical` check set to `true` |
| `seo_friendly_url_characters_check` | integer | *url characters check-up*<br>the number of pages with URLs containing only uppercase and lowercase Latin characters, digits and dashes |
| `seo_friendly_url_dynamic_check` | integer | *url dynamic check-up*<br>the number of pages with no dynamic parameters in the url |
| `seo_friendly_url_keywords_check` | integer | *url keyword check-up*<br>the number of pages that have URLs consistent with the `title` meta tag |
| `seo_friendly_url_relative_length_check` | integer | *url leghth check-up*<br>the number of pages with URLs no longer than 120 characters |
| `title_too_short` | integer | *pages with short titles*<br>the number of pages that have titles shorter than 30 characters;<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_content_encoding` | integer | *pages with no content encoding*<br>the number of pages with no [compression algorithm](http://www.iana.org/assignments/http-parameters/http-parameters.xhtml#content-coding) of the content |
| `high_waiting_time` | integer | *pages with high waiting time*<br>the number of pages with waiting time (aka Time to First Byte) exceeding 1.5 seconds |
| `high_loading_time` | integer | *pages with high loading time*<br>the number of pages with loading time exceeding 3 seconds |
| `is_redirect` | integer | *pages with redirects*<br>the number of pages with `3XX` redirects to other pages |
| `is_broken` | integer | *broken pages*<br>the number of pages with response codes less than `200` or greater than `400` |
| `is_4xx_code` | integer | *pages with `4xx` status codes*<br>the number of pages with `4xx` response codes |
| `is_5xx_code` | integer | *pages with `5xx` status codes*<br>the number of pages with `5xx` response codes |
| `is_www` | integer | *pages with www*<br>the number of pages on a `www` subdomain |
| `no_doctype` | integer | *pages with no doctype*<br>the number of pages without the`DOCTYPE` declaration |
| `no_encoding_meta_tag` | integer | *pages with no meta tag encoding*<br>the number of pages without `Content-Type`;<br>informative only if the encoding is not explicit in the `Content-Type` header;<br>for example: `Content-Type: "text/html; charset=utf8"`;<br>**Note:** available for pages with `canonical` check set to `true` |
| `high_content_rate` | integer | *pages with high content rate*<br>number of pages, which have the `plaintext size` to `page size` ratio of more than 0.9;<br>**Note:** available for pages with `canonical` check set to `true` |
| `low_character_count` | integer | *pages with low character count*<br>the number of pages containing less than 1024 characters;<br>**Note:** available for pages with `canonical` check set to `true` |
| `high_character_count` | integer | *pages with high character count*<br>the number of pages containing more than 256,000 characters;<br>**Note:** available for pages with `canonical` check set to `true` |
| `low_readability_rate` | integer | *pages with low readability rate*<br>the number of pages that scored less than 15 points on the [Flesch–Kincaid readability test](https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests);<br>**Note:** available for pages with `canonical` check set to `true` |
| `irrelevant_title` | integer | *pages with irrelevant titles*<br>the number of pages with `title` tags that are irrelevant to the content of the page<br>the relevance threshold is `0.3`<br>**Note:** available for pages with `canonical` check set to `true` |
| `deprecated_html_tags` | integer | *pages with deprecated tags*<br>the number of pages with [deprecated HTML tags](https://www.w3docs.com/learn-html/deprecated-html-tags.html);<br>**Note:** available for pages with `canonical` check set to `true` |
| `duplicate_title_tag` | integer | *pages with more than one title tag*<br>the number of pages that have more than one `title` tag;<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_title` | integer | *pages with no title*<br>the number of pages with empty or absent `title` tags;<br>**Note:** available for pages with `canonical` check set to `true` |
| `flash` | integer | *pages with flash*<br>the number of pages with flash elements |
| `lorem_ipsum` | integer | *pages with lorem ipsum*<br>the number of pages with *lorem ipsum* content;<br>**Note:** available for pages with `canonical` check set to `true` |
| `has_misspelling` | integer | *pages with misspelling*<br>the number of pages with *spelling* mistakes<br>informative if the `check_spell` was set to `true` in the POST array |
| `canonical_to_broken` | integer | *canonical pages pointing to broken pages*<br>the number of pages with a canonical link element pointing to a page that responds with a 404 error |
| `canonical_to_redirect` | integer | *canonical pages pointing to pages that redirect elsewhere*<br>the number of pages with a canonical link element pointing to a page that responds with a 3XX redirect |
| `has_links_to_redirects` | integer | *pages pointing to pages that redirect elsewhere*<br>the number of pages pointing to a page that responds with a 3XX redirect |
| `is_orphan_page` | integer | *pages with no internal links pointing to them*<br>the number of pages with no reference from other pages of the domain |
| `has_meta_refresh_redirect` | integer | *pages with meta refresh redirect*<br>the number of pages with <meta http-equiv=”refresh”> tag that instructs a browser to load another page after a specified time span;<br>**Note:** available for pages with `canonical` check set to `true` |
| `meta_charset_consistency` | integer | *pages with meta charset inconsistency*<br>the number of pages with charset encoding not matching the actual charset of the pages<br> |
| `size_greater_than_3mb` | integer | *pages with size larger than 3 MB*<br>the number of pages with size exceeding 3 MB;<br>**Note:** available for pages with `canonical` check set to `true` |
| `has_html_doctype` | integer | *pages with HTML doctype declaration*<br>the number of pages with the `DOCTYPE` declaration |
| `https_to_http_links` | integer | *pages with HTTPS protocol that link to pages with HTTP protocol*<br>the number of pages with secure HTTPS protocol that link to pages with unsecure HTTP protocol;<br>**Note:** available for pages with `canonical` check set to `true` |
| `has_render_blocking_resources` | integer | *pages with render-blocking resources*<br>the number of pages with render-blocking resources;<br>**Note:** available for pages with `canonical` check set to `true` |
| `redirect_chain` | integer | *pages with multiple redirects*<br>the number of pages with at least two redirects between the original page and the destination page |
| `canonical_chain` | integer | *pages with canonical pointing to a page that has a canonical pointing elsewhere*<br>the number of pages with a canonical link element pointing to a page that has a canonical pointing to a different page<br>e.g. page a is canonicalized to page b, which is canonicalized to page c |
| `is_link_relation_conflict` | integer | *pages on the target website that may have a link relation conflict*<br>for example, if `"is_link_relation_conflict": 1`, the target website has 1 page receiving at least one internal link with the `rel="nofollow"` attribute **and** at least one dofollow link |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Pages
*Source: [https://docs.dataforseo.com/v3/on_page/pages/](https://docs.dataforseo.com/v3/on_page/pages/)*
#### OnPage API Pages

This endpoint returns a list of crawled pages with on-page check-ups and other metrics related to the page performance.
Using this function you will get page-specific data with detailed information on how well your pages are optimized for search.

POSThttps://api.dataforseo.com/v3/on_page/pages

Pricing

Your account will not be charged for using this function. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page/onpage-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *ID of the task*<br>**required field**<br>you can get this ID in the response of the [Task POST](https://docs.dataforseo.com/v3/on_page/task_post/) endpoint<br>example:<br>“07131248-1535-0216-1000-17384017ad04” |
| `limit` | integer | *the maximum number of returned pages*<br>optional field<br>default value: `100`<br>maximum value: `1000` |
| `offset` | integer | *offset in the results array of returned pages*<br>optional field<br>default value: `0`<br>maximum value: `2000000`<br>if you specify the `10` value, the first ten pages in the results array will be omitted and the data will be provided for the successive pages |
| `filters` | array | *array of results filtering parameters*<br>optional field<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`regex`, `not_regex`, `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`, `like`, `not_like`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>example:<br>`["meta.external_links_count","<=",50]``["url","like","https://dataforseo.com/apis/dataforseo-labs-api"]``[["checks.high_waiting_time","=",false],<br>"and",["resource_type","=","html"]]``[["page_timing.duration_time","<",100],"and",[["checks.large_page_size","=",false],"or",["checks.high_waiting_time","=",false]]]`The full list of possible filters is available [by this link.](https://docs.dataforseo.com/v3/on_page/filters_and_thresholds/?bash) |
| `order_by` | array | *results sorting rules*<br>optional field<br>you can use the same values as in the `filters` array to sort the results<br>possible sorting types:<br>`asc` – results will be sorted in the ascending order<br>`desc` – results will be sorted in the descending order<br>you should use a comma to set up a sorting type<br>example:<br>`["meta.external_links_count,desc"]`<br>**note that you can set no more than three sorting rules in a single request**<br>you should use a comma to separate several sorting rules<br>example:<br>`["page_timing.dom_complete,asc","size,desc"]` |
| `search_after_token` | string | *token for subsequent requests*<br>optional field<br>provided in the identical filed of the response to each request;<br>use this parameter to avoid timeouts while trying to obtain over `20,000` results in a single request;<br>by specifying the unique `search_after_token` value from the response array, you will get the subsequent results of the initial task;<br>`search_after_token` values are unique for each subsequent task ;<br>**Note:** if the `search_after_token` is specified in the request, all other parameters should be identical to the previous request |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| ** `result`** | array | *array of results* |
| `crawl_progress` | string | *status of the crawling session*<br>possible values: `in_progress`, `finished` |
| `crawl_status` | object | *details of the crawling session* |
| `max_crawl_pages` | integer | *maximum number of pages to crawl*<br>indicates the `max_crawl_pages` limit you specified when setting a task |
| `pages_in_queue` | integer | *number of pages that are currently in the crawling queue* |
| `pages_crawled` | integer | *number of crawled pages* |
| `total_items_count` | integer | *total number of relevant items in the database* |
| `items_count` | integer | *number of items in the results array* |
| `items` | array | *items array* |
| ***‘html’ page*** | | |
| `resource_type` | string | *type of the returned resource = **‘html’*** |
| `status_code` | integer | *status code of the page* |
| `location` | string | *location header*<br>indicates the URL to redirect a page to |
| `url` | string | *page URL* |
| `meta` | object | *page properties*<br>the value depends on the `resource_type` |
| `title` | string | *page title* |
| `charset` | integer | *[code page](https://en.wikipedia.org/wiki/Code_page)*<br>example: `65001` |
| `follow` | boolean | *indicates whether a page’s ‘meta robots’ allows crawlers to follow the links on the page*<br>if `false`, the page’s ‘meta robots’ tag contains “nofollow” parameter instructing crawlers not to follow the links on the page |
| `generator` | string | *meta tag generator* |
| `htags` | object | *HTML header tags* |
| `description` | string | *content of the meta description tag* |
| `favicon` | string | *favicon of the page* |
| `meta_keywords` | string | *content of the `keywords` meta tag* |
| `canonical` | string | *canonical page* |
| `internal_links_count` | integer | *number of internal links on the page* |
| `external_links_count` | integer | *number of external links on the page* |
| `inbound_links_count` | integer | *number of internal links pointing at the page* |
| `images_count` | integer | *number of images on the page* |
| `images_size` | integer | *total size of images on the page measured in bytes* |
| `scripts_count` | integer | *number of scripts on the page* |
| `scripts_size` | integer | *total size of scripts on the page measured in bytes* |
| `stylesheets_count` | integer | *number of stylesheets on the page* |
| `stylesheets_size` | integer | *total size of stylesheets on the page measured in bytes* |
| `title_length` | integer | *length of the `title` tag in characters* |
| `description_length` | integer | *length of the `description` tag in characters* |
| `render_blocking_scripts_count` | integer | *number of scripts on the page that block page rendering* |
| `render_blocking_stylesheets_count` | integer | *number of CSS styles on the page that block page rendering* |
| `cumulative_layout_shift` | float | *Core Web Vitals metric measuring the layout stability of the page*<br>measures the sum total of all individual layout shift scores for every unexpected layout shift that occurs during the entire lifespan of the page. [Learn more.](https://web.dev/cls/) |
| `meta_title` | string | *meta title of the page*<br>meta tag in the head section of an HTML document that defines the title of a page |
| `content` | object | *overall information about content of the page* |
| `plain_text_size` | integer | *total size of the text on the page measured in bytes* |
| `plain_text_rate` | integer | *plaintext rate value*<br>`plain_text_size` to `size` ratio |
| `plain_text_word_count` | float | *number of words on the page* |
| `automated_readability_index` | float | *[Automated Readability Index](https://en.wikipedia.org/wiki/Automated_readability_index)* |
| `coleman_liau_readability_index` | float | *[Coleman–Liau Index](https://en.wikipedia.org/wiki/Coleman%E2%80%93Liau_index)* |
| `dale_chall_readability_index` | float | *[Dale–Chall Readability Index](https://en.wikipedia.org/wiki/Dale%E2%80%93Chall_readability_formula)* |
| `flesch_kincaid_readability_index` | float | *[Flesch–Kincaid Readability Index](https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests)* |
| `smog_readability_index` | float | *[SMOG Readability Index](https://en.wikipedia.org/wiki/SMOG)* |
| `description_to_content_consistency` | float | *consistency of the meta `description` tag with the page content*<br>measured from 0 to 1 |
| `title_to_content_consistency` | float | *consistency of the meta `title` tag with the page content*<br>measured from 0 to 1 |
| `meta_keywords_to_content_consistency` | float | *consistency of meta `keywords`tag with the page content*<br>measured from 0 to 1 |
| `deprecated_tags` | array | *deprecated tags on the page* |
| `duplicate_meta_tags` | array | *duplicate meta tags on the page* |
| `spell` | object | *spellcheck*<br>[hunspell](http://hunspell.github.io/) spellcheck errors |
| `hunspell_language_code` | string | *spellcheck language code* |
| `misspelled` | array | *array of misspelled words* |
| `word` | string | *misspelled word* |
| `social_media_tags` | object | *object of social media tags found on the page*<br>contains social media tags and their content<br>supported tags include but are not limited to [Open Graph](https://ogp.me/) and [Twitter card](https://developer.twitter.com/en/docs/twitter-for-websites/cards/guides/getting-started) |
| `page_timing` | object | *object of page load metrics* |
| `time_to_interactive` | integer | *[Time To Interactive (TTI)](https://web.dev/interactive/) metric*<br>the time it takes until the user can interact with a page (in milliseconds) |
| `dom_complete` | integer | *time to load resources*<br>the time it takes until the page and all of its subresources are downloaded (in milliseconds) |
| `largest_contentful_paint` | float | *Core Web Vitals metric measuring how fast the largest above-the-fold content element is displayed*<br>The amount of time (in milliseconds) to render the largest content element visible in the viewport, from when the user requests the URL. [Learn more](https://web.dev/lcp/). |
| `first_input_delay` | float | *Core Web Vitals metric indicating the responsiveness of a page*<br>The time (in milliseconds) from when a user first interacts with your page to the time when the browser responds to that interaction. [Learn more](https://web.dev/fid/). |
| `connection_time` | integer | *time to connect to a server*<br>the time it takes until the connection with a server is established (in milliseconds) |
| `time_to_secure_connection` | integer | *time to establish a secure connection*<br>the time it takes until the secure connection with a server is established (in milliseconds) |
| `request_sent_time` | integer | *time to send a request to a server*<br>the time it takes until the request to a server is sent (in milliseconds) |
| `waiting_time` | integer | *time to first byte [(TTFB)](https://en.wikipedia.org/wiki/Time_to_first_byte) in milliseconds* |
| `download_time` | integer | *time it takes for a browser to receive a response (in milliseconds)* |
| `duration_time` | integer | *total time it takes until a browser receives a complete response from a server (in milliseconds)* |
| `fetch_start` | integer | *time to start downloading the HTML resource*<br>the amount of time the browser needs to start downloading a page |
| `fetch_end` | integer | *time to complete downloading the HTML resource*<br>the amount of time the browser needs to complete downloading a page |
| `onpage_score` | float | *shows how page is optimized on a 100-point scale*<br>this field shows how page is optimized considering critical on-page issues and warnings detected;<br>`100` is the highest possible score that means the page does not have any critical on-page issues and important warnings;<br>learn more about how the metric is calculated in [this help center article](https://dataforseo.com/help-center/how-on-page-seo-score-is-calculated) |
| `total_dom_size` | integer | *total [DOM](https://developers.google.com/web/tools/chrome-devtools/dom) size of a page* |
| `custom_js_response` | string/object/integer | *the result of executing a specified JS script*<br>**note** that you should specify a `custom_js` field when [setting a task](https://docs.dataforseo.com/v3/on_page/task_post/) to receive this data and the field type and its value will totally depend on the script you specified;<br>you can also filter the results by this value specifying `filters` in the following way:<br>`["custom_js_response.url", "like", "pixel"]` |
| `custom_js_client_exception` | string | *error when executing a custom js*<br>if the error occurred when executing the script you specified in the `custom_js` field, the error message would be displayed here |
| `resource_errors` | object | *resource errors and warnings* |
| `errors` | array | *resource errors* |
| `line` | integer | *line where the error was found* |
| `column` | integer | *column where the error was found* |
| `message` | string | *text message of the error*<br>the full list of possible HTML errors can be found [here](https://github.com/AngleSharp/AngleSharp/blob/3968eb050e142b1d94550fba407afe772232b126/src/AngleSharp/Html/Parser/HtmlParseError.cs) |
| `status_code` | integer | *status code of the error*<br>possible values:<br>`0` — Unidentified Error;<br>`501` — Html Parse Error;<br>`1501` — JS Parse Error;<br>`2501` — CSS Parse Error;<br>`3501` — Image Parse Error;<br>`3502` — Image Scale Is Zero;<br>`3503` — Image Size Is Zero;<br>`3504` — Image Format Invalid |
| `warnings` | array | *resource warnings* |
| `line` | integer | *line the warning relates to*<br>note that if `"line": 0`, the warning relates to the whole page |
| `column` | integer | *column the warning relates to*<br>note that if `"column": 0`, the warning relates to the whole page |
| `message` | string | *text message of the warning*<br>possible messages:<br>`"Has node with more than 60 childs."` – HTML page has at least 1 tag nesting over 60 tags of the same level<br>`"Has more that 1500 nodes."` – DOM tree contains over 1,500 elements<br>`"HTML depth more than 32 tags."` – DOM depth exceeds 32 nodes |
| `status_code` | integer | *status code of the warning*<br>possible values:<br>`0` — Unidentified Warning;<br>`1` — Has node with more than 60 childs;<br>`2` — Has more that 1500 nodes;<br>`3` — HTML depth more than 32 tags |
| `broken_resources` | boolean | *indicates whether a page contains broken resources* |
| `broken_links` | boolean | *indicates whether a page contains broken links* |
| `duplicate_title` | boolean | *indicates whether a page has duplicate `title` tags* |
| `duplicate_description` | boolean | *indicates whether a page has a duplicate description* |
| `duplicate_content` | boolean | *indicates whether a page has duplicate content* |
| `click_depth` | integer | *number of clicks it takes to get to the page*<br>indicates the number of clicks from the homepage needed before landing at the target page |
| `size` | integer | *resource size*<br>indicates the size of a given page measured in bytes |
| `encoded_size` | integer | *page size after encoding*<br>indicates the size of the encoded page measured in bytes |
| `total_transfer_size` | integer | *compressed page size*<br>indicates the compressed size of a given page |
| `fetch_time` | string | *date and time when a resource was fetched*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `cache_control` | object | *instructions for caching* |
| `cachable` | boolean | *indicates whether the page is cacheable* |
| `ttl` | integer | *time to live*<br>the amount of time the browser caches a resource |
| `checks` | object | *website checks*<br>on-page check-ups related to the page |
| `no_content_encoding` | boolean | *page with no content encoding*<br>indicates whether a page has no [compression algorithm](http://www.iana.org/assignments/http-parameters/http-parameters.xhtml#content-coding) of the content |
| `high_loading_time` | boolean | *page with high loading time*<br>indicates whether a page loading time exceeds 3 seconds |
| `is_redirect` | boolean | *page with redirects*<br>indicates whether a page has `3XX` redirects to other pages |
| `is_4xx_code` | boolean | *page with `4xx` status codes*<br>indicates whether a page has `4xx` response code |
| `is_5xx_code` | boolean | *page with `5xx` status codes*<br>indicates whether a page has `5xx` response code |
| `is_broken` | boolean | *broken page*<br>indicates whether a page returns a response code less than `200` or greater than `400` |
| `is_www` | boolean | *page with www*<br>indicates whether a page is on a `www` subdomain |
| `is_https` | boolean | *page with the https protocol* |
| `is_http` | boolean | *page with the http protocol* |
| `high_waiting_time` | boolean | *page with high waiting time*<br>indicates whether a page waiting time (aka Time to First Byte) exceeds 1.5 seconds |
| `has_micromarkup` | boolean | *page contains [microdata markup](https://en.wikipedia.org/wiki/Microdata_(HTML))* |
| `has_micromarkup_errors` | boolean | *page contains microdata markup errors* |
| `no_doctype` | boolean | *page with no doctype*<br>indicates whether a page is without the `<!DOCTYPE HTML>` declaration |
| `canonical` | boolean | *page is canonical* |
| `no_encoding_meta_tag` | boolean | *page with no meta tag encoding*<br>indicates whether a page is without `Content-Type`;<br>informative only if the encoding is not explicit in the `Content-Type` header;<br>for example: `Content-Type: "text/html; charset=utf8"`;<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_h1_tag` | boolean | *page with empty or absent h1 tags*<br>**Note:** available for pages with `canonical` check set to `true` |
| `https_to_http_links` | boolean | *HTTPS page has links to HTTP pages*<br>if `true`, this `HTTPS` page has links to `HTTP` pages;<br>**Note:** available for pages with `canonical` check set to `true` |
| `has_html_doctype` | boolean | *page with HTML doctype declaration*<br>if `true`, the page has HTML `DOCTYPE` declaration |
| `size_greater_than_3mb` | boolean | *page with size larger than 3 MB*<br>if `true`, the page size is exceeding 3 MB;<br>**Note:** available for pages with `canonical` check set to `true` |
| `meta_charset_consistency` | boolean | *consistency between charset encoding and page charset*<br>if `true`, the page’s charset encoding doesn’t match the actual charset of the page;<br>**Note:** available for pages with `canonical` check set to `true` |
| `has_meta_refresh_redirect` | boolean | *pages with meta refresh redirect*<br>if `true`, the page has <meta http-equiv=”refresh”> tag that instructs a browser to load another page after a specified time span;<br>**Note:** available for pages with `canonical` check set to `true` |
| `has_render_blocking_resources` | boolean | *page with render-blocking resources*<br>if `true`, the page has render-blocking scripts or stylesheets;<br>**Note:** available for pages with `canonical` check set to `true` |
| `from_sitemap` | boolean | *resource was found on website’s sitemap<br>if `true`, the resource was found on the sitemap of the website<br>* |
| `redirect_chain` | boolean | *page with multiple redirects*<br>if `true`, there were at least two redirects before our crawler reached this page |
| `low_content_rate` | boolean | *page with low content rate*<br>indicates whether a page has the `plaintext size` to `page size` ratio of less than 0.1;<br>**Note:** available for pages with `canonical` check set to `true` |
| `high_content_rate` | boolean | *page with high content rate*<br>indicates whether a page has the `plaintext size` to `page size` ratio of more than 0.9;<br>**Note:** available for pages with `canonical` check set to `true` |
| `low_character_count` | boolean | *indicates whether the page has less than 1024 characters*<br>**Note:** available for pages with `canonical` check set to `true` |
| `high_character_count` | boolean | *indicates whether the page has more than 256,000 characters*<br>**Note:** available for pages with `canonical` check set to `true` |
| `small_page_size` | boolean | *indicates whether a page is too small*<br>the value will be `true` if a page size is smaller than 1024 bytes;<br>**Note:** available for pages with `canonical` check set to `true` |
| `large_page_size` | boolean | *indicates whether a page is too heavy*<br>the value will be `true` if a page size exceeds 1 megabyte;<br>**Note:** available for pages with `canonical` check set to `true` |
| `low_readability_rate` | boolean | *page with a low readability rate*<br>indicates whether a page is scored less than 15 points on the [Flesch–Kincaid readability test](https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests);<br>**Note:** available for pages with `canonical` check set to `true` |
| `irrelevant_description` | boolean | *page with irrelevant description*<br>indicates whether a page `description` tag is irrelevant to the content of a page;<br>the relevance threshold is `0.2`;<br>**Note:** available for pages with `canonical` check set to `true` |
| `irrelevant_title` | boolean | *page with irrelevant title*<br>indicates whether a page `title` tag is irrelevant to the content of the page;<br>the relevance threshold is `0.3`;<br>**Note:** available for pages with `canonical` check set to `true` |
| `irrelevant_meta_keywords` | boolean | *page with irrelevant meta keywords*<br>indicates whether a page `keywords` tags are irrelevant to the content of a page;<br>the relevance threshold is `0.6`;<br>**Note:** available for pages with `canonical` check set to `true` |
| `title_too_long` | boolean | *page with a long title*<br>indicates whether the content of the `title` tag exceeds 65 characters;<br>**Note:** available for pages with `canonical` check set to `true` |
| `has_meta_title` | boolean | *page has a meta title*<br>indicates whether the HTML of a page contains the `meta_title` tag;<br>**Note:** available for pages with `canonical` check set to `true` |
| `title_too_short` | boolean | *page with short titles*<br>indicates whether the content of `title` tag is shorter than 30 characters;<br>**Note:** available for pages with `canonical` check set to `true` |
| `deprecated_html_tags` | boolean | *page with deprecated tags*<br>indicates whether a page has [deprecated HTML tags](https://www.w3docs.com/learn-html/deprecated-html-tags.html);<br>**Note:** available for pages with `canonical` check set to `true` |
| `duplicate_meta_tags` | boolean | *page with duplicate meta tags*<br>indicates whether a page has more than one meta tag of the same type;<br>**Note:** available for pages with `canonical` check set to `true` |
| `duplicate_title_tag` | boolean | *page with more than one title tag*<br>indicates whether a page has more than one `title` tag;<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_image_alt` | boolean | *images without `alt` tags*<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_image_title` | boolean | *images without `title` tags*<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_description` | boolean | *pages with no description*<br>indicates whether a page has an empty or absent `description` meta tag;<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_title` | boolean | *page with no title*<br>indicates whether a page has an empty or absent `title` tag;<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_favicon` | boolean | *page with no favicon*<br>**Note:** available for pages with `canonical` check set to `true` |
| `seo_friendly_url` | boolean | *page with seo-frienldy URL*<br>the ‘SEO-friendliness’ of a page URL is checked by four parameters:<br>– the length of the relative path is less than 120 characters<br>– no special characters<br>– no dynamic parameters<br>– relevance of the URL to the page<br>if at least one of them is failed then such URL is considered as not ‘SEO-friendly’<br>**Note:** available for pages with `canonical` check set to `true` |
| `flash` | boolean | *page with flash*<br>indicates whether a page has flash elements |
| `frame` | boolean | *page with frames*<br>indicates whether a page contains `frame`, `iframe`, `frameset` tags |
| `lorem_ipsum` | boolean | *page with lorem ipsum*<br>indicates whether a page has *lorem ipsum* content;<br>**Note:** available for pages with `canonical` check set to `true` |
| `has_misspelling` | boolean | *page with misspelling*<br>indicates whether a page has *spelling* mistakes<br>informative if the `check_spell` was set to `true` in the POST array |
| `seo_friendly_url_characters_check` | boolean | *URL characters check-up*<br>indicates whether a page URL containing only uppercase and lowercase Latin characters, digits and dashes |
| `seo_friendly_url_dynamic_check` | boolean | *URL dynamic check-up*<br>the value will be `true` if a page has no dynamic parameters in the url |
| `seo_friendly_url_keywords_check` | boolean | *URL keyword check-up*<br>indicates whether a page URL is consistent with the `title` meta tag |
| `seo_friendly_url_relative_length_check` | boolean | *URL length check-up*<br>the value will be `true` if a page URL no longer than 120 characters |
| `is_orphan_page` | boolean | *page with no internal links pointing to it*<br>`true` if the page has no reference from other pages of the domain<br>**Note:** to use this field, set the `respect_sitemap` parameter in the [POST request](https://docs.dataforseo.com/v3/on_page/task_post/?bash) to `true` |
| `is_link_relation_conflict` | boolean | *mix of both followed and nofollowed incoming internal links*<br>`true` if the page receives at least one link with the `rel="nofollow"` attribute and at least one dofollow link |
| `has_links_to_redirects` | boolean | *page is pointing to a page that redirect elsewhere*<br>`true` if the page is pointing to a page that responds with a 3XX redirect |
| `canonical_chain` | boolean | *pages with canonical pointing to a page that has a canonical pointing elsewhere*<br>`true` if the page has a canonical link element pointing to a page that has a canonical pointing to a different page<br>e.g. page a is canonicalized to page b, which is canonicalized to page c |
| `canonical_to_redirect` | boolean | *canonical page pointing to a page that redirects elsewhere*<br>`true` if the page has a canonical link element pointing to a page that responds with a 3XX redirect |
| `canonical_to_broken` | boolean | *canonical link pointing to a broken page*<br>`true` if the page has a a canonical link pointing to a page that responds with a 4xx or 5xx response codes |
| `recursive_canonical` | boolean | *recursive canonical error*<br>`true` if the page contains `rel="canonical"` tag to another page, which in turn, refers back to the initial page |
| `content_encoding` | string | *type of encoding* |
| `media_type` | string | *types of media used to display a page* |
| `server` | string | *server version* |
| `is_resource` | boolean | *indicates whether a page is a single resource* |
| `url_length` | integer | *page URL length in characters* |
| `relative_url_length` | integer | *relative URL length in characters* |
| `last_modified` | object | *contains data on changes related to the resource*<br>if there is no data, the value will be `null` |
| `header` | string | *date and time when the header was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| `sitemap` | string | *date and time when the sitemap was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| `meta_tag` | string | *date and time when the meta tag was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| ***‘broken’ page*** | | |
| `resource_type` | string | *type of the returned resource = **‘broken’*** |
| `status_code` | integer | *status code of the page* |
| `location` | string | *location header*<br>indicates the URL to redirect a page to |
| `url` | string | *page URL* |
| `size` | integer | *resource size*<br>indicates the size of a given page measured in bytes |
| `encoded_size` | integer | *page size after encoding*<br>indicates the size of the encoded page measured in bytes |
| `total_transfer_size` | integer | *compressed page size*<br>indicates the compressed size of a given page |
| `fetch_time` | string | *date and time when a resource was fetched*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `fetch_timing` | object | *time range within which a result was fetched* |
| `duration_time` | integer | *indicates how many seconds it took to download a page* |
| `fetch_start` | integer | *time to start downloading the HTML resource*<br>the amount of time the browser needs to start downloading a page |
| `fetch_end` | integer | *time to complete downloading the HTML resource*<br>the amount of time the browser needs to complete downloading a page |
| `resource_errors` | object | *resource errors and warnings* |
| `errors` | array | *resource errors* |
| `line` | integer | *line where the error was found* |
| `column` | integer | *column where the error was found* |
| `message` | string | *text message of the error*<br>the full list of possible HTML errors can be found [here](https://github.com/AngleSharp/AngleSharp/blob/3968eb050e142b1d94550fba407afe772232b126/src/AngleSharp/Html/Parser/HtmlParseError.cs) |
| `status_code` | integer | *status code of the error*<br>possible values:<br>`0` — Unidentified Error;<br>`501` — Html Parse Error;<br>`1501` — JS Parse Error;<br>`2501` — CSS Parse Error;<br>`3501` — Image Parse Error;<br>`3502` — Image Scale Is Zero;<br>`3503` — Image Size Is Zero;<br>`3504` — Image Format Invalid |
| `warnings` | array | *resource warnings* |
| `line` | integer | *line the warning relates to*<br>note that if `"line": 0`, the warning relates to the whole page |
| `column` | integer | *columnthe warning relates to*<br>note that if `"column": 0`, the warning relates to the whole page |
| `message` | string | *text message of the warning*<br>possible messages:<br>`"Has node with more than 60 childs."` – HTML page has at least 1 tag nesting over 60 tags of the same level<br>`"Has more that 1500 nodes."` – DOM tree contains over 1,500 elements<br>`"HTML depth more than 32 tags."` – DOM depth exceeds 32 nodes |
| `status_code` | integer | *status code of the warning*<br>possible values:<br>`0` — Unidentified Warning;<br>`1` — Has node with more than 60 childs;<br>`2` — Has more that 1500 nodes;<br>`3` — HTML depth more than 32 tags |
| `cache_control` | object | *instructions for caching* |
| `cachable` | boolean | *indicates whether the page is cacheable* |
| `ttl` | integer | *time to live*<br>the amount of time the browser caches a resource |
| `checks` | object | *on-page check-ups* |
| `no_content_encoding` | boolean | *page with no content encoding*<br>indicates whether a page has no [compression algorithm](http://www.iana.org/assignments/http-parameters/http-parameters.xhtml#content-coding) of the content |
| `high_loading_time` | boolean | *page with high loading time*<br>indicates whether a page loading time exceeds 3 seconds |
| `is_redirect` | boolean | *page with redirects*<br>indicates whether a page has `3XX` redirects to other pages |
| `is_4xx_code` | boolean | *page with with `4xx` status code*<br>indicates whether a page has `4XX` response code |
| `is_5xx_code` | boolean | *page with `5xx` status code*<br>indicates whether a page has `5XX` response code |
| `is_broken` | boolean | *broken page*<br>indicates whether a page returns a response code less than `200` or greater than `400` |
| `is_www` | boolean | *page with www*<br>indicates whether a page is on a `www` subdomain |
| `is_https` | boolean | *page with the https protocol* |
| `is_http` | boolean | *page with the http protocol* |
| `is_orphan_page` | boolean | *page with no internal links pointing to it*<br>`true` if the page has no reference from other pages of the domain<br>**Note:** to use this field, set the `respect_sitemap` parameter in the [POST request](https://docs.dataforseo.com/v3/on_page/task_post/?bash) to `true` |
| `is_link_relation_conflict` | boolean | *mix of both followed and nofollowed incoming internal links*<br>`true` if the page receives at least one link with the `rel="nofollow"` attribute and at least one dofollow link |
| `has_links_to_redirects` | boolean | *page is pointing to a page that redirect elsewhere*<br>`true` if the page is pointing to a page that responds with a 3XX redirect |
| `from_sitemap` | boolean | *resource was found on website’s sitemap<br>if `true`, the resource was found on the sitemap of the website<br>* |
| `canonical_chain` | boolean | *pages with canonical pointing to a page that has a canonical pointing elsewhere*<br>`true` if the page has a canonical link element pointing to a page that has a canonical pointing to a different page<br>e.g. page a is canonicalized to page b, which is canonicalized to page c |
| `canonical_to_redirect` | boolean | *canonical page pointing to a page that redirects elsewhere*<br>`true` if the page has a canonical link element pointing to a page that responds with a 3XX redirect |
| `canonical_to_broken` | boolean | *canonical link pointing to a broken page*<br>`true` if the page has a canonical link pointing to a page that responds with a 4xx or 5xx response codes |
| `content_encoding` | string | *type of encoding* |
| `media_type` | string | *types of media used to display a page*<br>example: `"text/html"` |
| `server` | string | *server version* |
| `is_resource` | boolean | *indicates whether a page is a single resource* |
| `last_modified` | object | *contains data on changes related to the resource*<br>if there is no data, the value will be `null` |
| `header` | string | *date and time when the header was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| `sitemap` | string | *date and time when the sitemap was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| `meta_tag` | string | *date and time when the meta tag was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| ***‘redirect’ page*** | | |
| `resource_type` | string | *type of the returned resource = **‘redirect’*** |
| `status_code` | integer | *status code of the page* |
| `location` | string | *location header*<br>**target URL** for “redirect” resources |
| `url` | string | *page url*<br>**source URL** for “redirect” resources |
| `size` | integer | *resource size*<br>indicates the size of a given page measured in bytes<br>equals `0` for “redirect” resources |
| `encoded_size` | integer | *page size after encoding*<br>equals `0` for “redirect” resources |
| `total_transfer_size` | integer | *compressed page size*<br>indicates the compressed size of a given page |
| `fetch_time` | string | *date and time when a resource was fetched*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `fetch_timing` | object | *time range within which a result was fetched* |
| `duration_time` | integer | *indicates how many seconds it took to download a page* |
| `fetch_start` | integer | *time to start downloading the HTML resource*<br>the amount of time the browser needs to start downloading a page |
| `fetch_end` | integer | *time to complete downloading the HTML resource*<br>the amount of time the browser needs to complete downloading a page |
| `resource_errors` | object | *resource errors and warnings* |
| `errors` | array | *resource errors* |
| `line` | integer | *line where the error was found* |
| `column` | integer | *column where the error was found* |
| `message` | string | *text message of the error*<br>the full list of possible HTML errors can be found [here](https://github.com/AngleSharp/AngleSharp/blob/3968eb050e142b1d94550fba407afe772232b126/src/AngleSharp/Html/Parser/HtmlParseError.cs) |
| `status_code` | integer | *status code of the error*<br>possible values:<br>`0` — Unidentified Error;<br>`501` — Html Parse Error;<br>`1501` — JS Parse Error;<br>`2501` — CSS Parse Error;<br>`3501` — Image Parse Error;<br>`3502` — Image Scale Is Zero;<br>`3503` — Image Size Is Zero;<br>`3504` — Image Format Invalid |
| `warnings` | array | *resource warnings* |
| `line` | integer | *line the warning relates to*<br>note that if `"line": 0`, the warning relates to the whole page |
| `column` | integer | *column the warning relates to*<br>note that if `"column": 0`, the warning relates to the whole page |
| `message` | string | *text message of the warning*<br>possible messages:<br>`"Has node with more than 60 childs."` – HTML page has at least 1 tag nesting over 60 tags of the same level<br>`"Has more that 1500 nodes."` – DOM tree contains over 1,500 elements<br>`"HTML depth more than 32 tags."` – DOM depth exceeds 32 nodes |
| `status_code` | integer | *status code of the warning*<br>possible values:<br>`0` — Unidentified Warning;<br>`1` — Has node with more than 60 childs;<br>`2` — Has more that 1500 nodes;<br>`3` — HTML depth more than 32 tags |
| `cache_control` | object | *instructions for caching* |
| `cachable` | boolean | *indicates whether the page is cacheable* |
| `ttl` | integer | *time to live*<br>the amount of time the browser caches a resource |
| `checks` | object | *on-page check-ups* |
| `no_content_encoding` | boolean | *page with no content encoding*<br>indicates whether a page has no [compression algorithm](http://www.iana.org/assignments/http-parameters/http-parameters.xhtml#content-coding) of the content |
| `high_loading_time` | boolean | *page with high loading time*<br>indicates whether a page loading time exceeds 3 seconds |
| `is_redirect` | boolean | *page with redirects*<br>indicates whether a page has `3XX` redirects to other pages |
| `is_4xx_code` | boolean | *page with `4xx` status codes*<br>indicates whether a page has `4xx` response code |
| `is_5xx_code` | boolean | *page with `5xx` status codes*<br>indicates whether a page has `5xx` response code |
| `is_broken` | boolean | *broken page*<br>indicates whether a page returns a response code less than `200` or greater than `400` |
| `is_www` | boolean | *page with www*<br>indicates whether a page is on a `www` subdomain |
| `is_https` | boolean | *page with the https protocol* |
| `is_http` | boolean | *page with the http protocol* |
| `is_orphan_page` | boolean | *page with no internal links pointing to it*<br>`true` if the page has no reference from other pages of the domain<br>**Note:** to use this field, set the `respect_sitemap` parameter in the [POST request](https://docs.dataforseo.com/v3/on_page/task_post/?bash) to `true` |
| `is_link_relation_conflict` | boolean | *mix of both followed and nofollowed incoming internal links*<br>`true` if the page receives at least one link with the `rel="nofollow"` attribute and at least one dofollow link |
| `has_links_to_redirects` | boolean | *page is pointing to a page that redirect elsewhere*<br>`true` if the page is pointing to a page that responds with a 3XX redirect |
| `from_sitemap` | boolean | *resource was found on website’s sitemap<br>if `true`, the resource was found on the sitemap of the website<br>* |
| `canonical_chain` | boolean | *pages with canonical pointing to a page that has a canonical pointing elsewhere*<br>`true` if the page has a canonical link element pointing to a page that has a canonical pointing to a different page<br>e.g. page a is canonicalized to page b, which is canonicalized to page c |
| `canonical_to_redirect` | boolean | *canonical page pointing to a page that redirects elsewhere*<br>`true` if the page has a canonical link element pointing to a page that responds with a 3XX redirect |
| `canonical_to_broken` | boolean | *canonical link pointing to a broken page*<br>`true` if the page has a canonical link pointing to a page that responds with a 4xx or 5xx response codes |
| `content_encoding` | string | *type of encoding* |
| `media_type` | string | *types of media used to display a page*<br>example: `"text/html"` |
| `server` | string | *server version* |
| `is_resource` | boolean | *indicates whether a page is a single resource* |
| `last_modified` | object | *contains data on changes related to the resource*<br>if there is no data, the value will be `null` |
| `header` | string | *date and time when the header was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| `sitemap` | string | *date and time when the sitemap was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| `meta_tag` | string | *date and time when the meta tag was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| ***resources*** | | *Note: the following types of resources will be displayed only if the first URL to crawl is a script, image, or stylesheet* |
| `resource_type` | string | *type of the returned resource*<br>possible types: `script`, `image`, `stylesheet` |
| `meta` | object | *resource properties*<br>available only for items with the following `resource_type`: `image` |
| `alternative_text` | string | *content of the image `alt` attribute* |
| `title` | string | *title* |
| `original_width` | integer | *original image width in px* |
| `original_height` | integer | *original image height in px* |
| `width` | integer | *image width in px* |
| `height` | integer | *image height in px* |
| `status_code` | integer | *status code of the page where a given resource is located* |
| `location` | string | *location header*<br>indicates the URL to redirect a page to |
| `url` | string | *resource URL* |
| `size` | integer | *resource size*<br>indicates the size of a given resource measured in bytes |
| `encoded_size` | integer | *resource size after encoding*<br>indicates the size of the encoded resource measured in bytes |
| `total_transfer_size` | integer | *compressed resource size*<br>indicates the compressed size of a given resource in bytes |
| `fetch_time` | string | *date and time when a resource was fetched*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2021-02-17 13:54:15 +00:00` |
| `fetch_timing` | object | *resource fetching time range* |
| `duration_time` | integer | *indicates how many milliseconds it took to fetch a resource* |
| `fetch_start` | integer | *time to start downloading the resource*<br>the amount of time a browser needs to start downloading a resource |
| `fetch_end` | integer | *time to complete downloading the resource*<br>the amount of time a browser needs to complete downloading a resource |
| `cache_control` | object | *instructions for caching* |
| `cachable` | boolean | *indicates whether the resource is cacheable* |
| `ttl` | integer | *time to live*<br>the amount of time it takes for the browser to cache a resource; measured in milliseconds |
| `checks` | object | *resource check-ups*<br>contents of the array depend on the `resource_type` |
| `no_content_encoding` | boolean | *resource with no content encoding*<br>indicates whether a page has no [compression algorithm](http://www.iana.org/assignments/http-parameters/http-parameters.xhtml#content-coding) of the content; |
| `high_loading_time` | boolean | *resource with high loading time*<br>indicates whether a resource loading time exceeds 3 seconds; |
| `is_redirect` | boolean | *resource with redirects*<br>indicates whether a page with a resource has `3XX` redirects to other pages; |
| `is_4xx_code` | boolean | *resource with `4xx` status codes*<br>indicates whether a resource has `4xx` response code |
| `is_5xx_code` | boolean | *resource with `5xx` status codes*<br>indicates whether a resource has `5xx` response code |
| `is_broken` | boolean | *broken resource*<br>indicates whether a page with this resource returns `4xx`, `5xx` response codes or has broken elements inside the resource |
| `is_www` | boolean | *page with www*<br>indicates whether a page with this resource is on a `www` subdomain |
| `is_https` | boolean | *page with the https protocol* |
| `is_http` | boolean | *page with the http protocol* |
| `is_minified` | boolean | *resource is minified*<br>indicates whether the content of a stylesheet or script is minified;<br>available for items with the following `resource_type`: `stylesheet`, `script` |
| `has_subrequests` | boolean | *resource contains subrequests*<br>indicates whether the content of a stylesheet or script contain additional requests;<br>available for items with the following `resource_type`: `stylesheet`, `script` |
| `has_redirect` | boolean | *resource has a redirect*<br>available for items with the following `resource_type`: `script`, `image`;<br>if the `resource_type` is `image`, this field will indicate whether other pages and/or resources have redirects pointing at the image;<br>if the `resource_type` is `script`, this field will indicate whether the script contains a redirect |
| `original_size_displayed` | boolean | *image desplayes in its original size*<br>indicates whether the image is displayed in its original size;<br>available only for items with the following `resource_type`: `image` |
| `recursive_canonical` | boolean | *recursive canonical error*<br>`true` if the page contains `rel="canonical"` tag to another page, which in turn, refers back to the initial page |
| `canonical_chain` | boolean | *pages with canonical pointing to a page that has a canonical pointing elsewhere*<br>`true` if the page has a canonical link element pointing to a page that has a canonical pointing to a different page<br>e.g. page a is canonicalized to page b, which is canonicalized to page c |
| `canonical_to_redirect` | boolean | *canonical page pointing to a page that redirects elsewhere*<br>`true` if the page has a canonical link element pointing to a page that responds with a 3XX redirect |
| `canonical_to_broken` | boolean | *canonical link pointing to a broken page*<br>`true` if the page has a a canonical link pointing to a page that responds with a 4xx or 5xx response codes |
| `has_links_to_redirects` | boolean | *page is pointing to a page that redirect elsewhere*<br>`true` if the page is pointing to a page that responds with a 3XX redirect |
| `is_orphan_page` | boolean | *page with no internal links pointing to it*<br>`true` if the page has no reference from other pages of the domain<br>**Note:** to use this field, set the `respect_sitemap` parameter in the [POST request](https://docs.dataforseo.com/v3/on_page/task_post/?bash) to `true` |
| `is_link_relation_conflict` | boolean | *mix of both followed and nofollowed incoming internal links*<br>`true` if the page receives at least one link with the `rel="nofollow"` attribute and at least one dofollow link |
| `from_sitemap` | boolean | *resource was found on website’s sitemap<br>if `true`, the resource was found on the sitemap of the website<br>* |
| `resource_errors` | object | *resource errors and warnings* |
| `errors` | array | *resource errors* |
| `line` | integer | *line where the error was found* |
| `column` | integer | *column where the error was found* |
| `message` | string | *text message of the error*<br>the full list of possible HTML errors can be found [here](https://github.com/AngleSharp/AngleSharp/blob/3968eb050e142b1d94550fba407afe772232b126/src/AngleSharp/Html/Parser/HtmlParseError.cs) |
| `status_code` | integer | *status code of the error*<br>possible values:<br>`0` — Unidentified Error;<br>`501` — Html Parse Error;<br>`1501` — JS Parse Error;<br>`2501` — CSS Parse Error;<br>`3501` — Image Parse Error;<br>`3502` — Image Scale Is Zero;<br>`3503` — Image Size Is Zero;<br>`3504` — Image Format Invalid |
| `warnings` | array | *resource warnings* |
| `line` | integer | *line the warning relates to*<br>note that if `"line": 0`, the warning relates to the whole page |
| `column` | integer | *column the warning relates to*<br>note that if `"column": 0`, the warning relates to the whole page |
| `message` | string | *text message of the warning*<br>possible messages:<br>`"Has node with more than 60 childs."` – HTML page has at least 1 tag nesting over 60 tags of the same level<br>`"Has more that 1500 nodes."` – DOM tree contains over 1,500 elements<br>`"HTML depth more than 32 tags."` – DOM depth exceeds 32 nodes |
| `status_code` | integer | *status code of the warning*<br>possible values:<br>`0` — Unidentified Warning;<br>`1` — Has node with more than 60 childs;<br>`2` — Has more that 1500 nodes;<br>`3` — HTML depth more than 32 tags |
| `content_encoding` | string | *type of encoding* |
| `media_type` | string | *types of media used to display a resource* |
| `accept_type` | string | *indicates the expected type of resource*<br>for example, if `"resource_type": "broken"`, `accept_type` will indicate the type of the broken resource<br>possible values:<br>`any`, `none`, `image`, `sitemap`, `robots`, `script`, `stylesheet`, `redirect`, `html`, `text`, `other`, `font` |
| `server` | string | *server version* |
| `last_modified` | object | *contains data on changes related to the resource*<br>if there is no data, the value will be `null` |
| `header` | string | *date and time when the header was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| `sitemap` | string | *date and time when the sitemap was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| `meta_tag` | string | *date and time when the meta tag was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Pages By Resource
*Source: [https://docs.dataforseo.com/v3/on_page/page_by_resource/](https://docs.dataforseo.com/v3/on_page/page_by_resource/)*
#### OnPage API Pages By Resource

This endpoint will return the list of pages where a specific resource is located. Using this function you will also get the data related to the pages that contain a specified resource.
You can get the URL of a resource using the [Resources](https://docs.dataforseo.com/v3/on_page/resources/) endpoint.

POSThttps://api.dataforseo.com/v3/on_page/pages_by_resource

Pricing

Your account will not be charged for using this function. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page/onpage-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *ID of the task*<br>**required field**<br>you can get this ID in the response of the [Task POST](https://docs.dataforseo.com/v3/on_page/task_post/) endpoint<br>example:<br>“07131248-1535-0216-1000-17384017ad04” |
| `url` | string | *resource URL*<br>**required field**<br>you can get this URL in the response of the [Resources](https://docs.dataforseo.com/v3/on_page/resources/) endpoint<br>example:<br>`https://ajax.googleapis.com/ajax/libs/jquery/1.12.4/jquery.min.js` |
| `limit` | integer | *the maximum number of returned pages*<br>optional field<br>default value: `100`<br>maximum value: `1000` |
| `offset` | integer | *offset in the results array of returned pages*<br>optional field<br>default value: `0`<br>maximum value: `2000000`<br>if you specify the `10` value, the first ten pages in the results array will be omitted and the data will be provided for the successive pages |
| `filters` | array | *array of results filtering parameters*<br>optional field<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`regex`, `not_regex`, `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`, `like`, `not_like`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>example:<br>`["meta.external_links_count","<=",50]``["url","like","https://dataforseo.com/apis/dataforseo-labs-api"]`<br>`[["checks.high_waiting_time","=",false],<br>"and",["resource_type","=","html"]]`<br>`[["page_timing.duration_time","<",100],"and",[["checks.large_page_size","=",false],"or",["checks.high_waiting_time","=",false]]]`<br>The full list of possible filters is available [by this link.](https://docs.dataforseo.com/v3/on_page/filters_and_thresholds/?bash) |
| `order_by` | array | *results sorting rules*<br>optional field<br>you can use the same values as in the `filters` array to sort the results<br>possible sorting types:<br>`asc` – results will be sorted in the ascending order<br>`desc` – results will be sorted in the descending order<br>you should use a comma to set up a sorting type<br>example:<br>`["meta.external_links_count,desc"]`<br>**note that you can set no more than three sorting rules in a single request**<br>you should use a comma to separate several sorting rules<br>example:<br>`["page_timing.dom_complete,asc","size,desc"]` |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| ** `result`** | array | *array of results* |
| `crawl_progress` | string | *status of the crawling session*<br>possible values: `in_progress`, `finished` |
| `crawl_status` | object | *details of the crawling session* |
| `max_crawl_pages` | integer | *maximum number of pages to crawl*<br>indicates the `max_crawl_pages` limit you specified when setting a task |
| `pages_in_queue` | integer | *number of pages that are currently in the crawling queue* |
| `pages_crawled` | integer | *number of crawled pages* |
| `total_items_count` | integer | *total number of relevant items in the database* |
| `items_count` | integer | *number of items in the results array* |
| `items` | array | *items array* |
| ***‘html’ page*** | | |
| `resource_type` | string | *type of the returned resource = **‘html’*** |
| `status_code` | integer | *status code of the page* |
| `location` | string | *location header*<br>indicates the URL to redirect a page to |
| `url` | string | *page URL* |
| `meta` | object | *page properties*<br>the value depends on the `resource_type` |
| `title` | integer | *page title* |
| `charset` | integer | *[code page](https://en.wikipedia.org/wiki/Code_page)*<br>example: `65001` |
| `follow` | boolean | *indicates whether a page’s ‘meta robots’ allows crawlers to follow the links on the page*<br>if `false`, the page’s ‘meta robots’ tag contains “nofollow” parameter instructing crawlers not to follow the links on the page |
| `generator` | string | *meta tag generator* |
| `htags` | object | *HTML header tags* |
| `description` | string | *content of the `description` meta tag* |
| `favicon` | string | *favicon of the page* |
| `meta_keywords` | string | *content of the `keywords` meta tag* |
| `canonical` | string | *canonical page* |
| `internal_links_count` | integer | *number of internal links on the page* |
| `external_links_count` | integer | *number of external links on the page* |
| `images_count` | integer | *number of images on the page* |
| `images_size` | integer | *total size of images on the page measured in bytes* |
| `scripts_count` | integer | *number of scripts on the page* |
| `scripts_size` | integer | *total size of scripts on the page measured in bytes* |
| `stylesheets_count` | integer | *number of stylesheets on the page* |
| `stylesheets_size` | integer | *total size of stylesheets on the page measured in bytes* |
| `title_length` | integer | *length of the `title` tag in characters* |
| `description_length` | integer | *length of the `description` tag in characters* |
| `render_blocking_scripts_count` | integer | *number of scripts on the page that block page rendering* |
| `render_blocking_stylesheets_count` | integer | *number of CSS styles on the page that block page rendering* |
| `cumulative_layout_shift` | float | *Core Web Vitals metric measuring the layout stability of a page*<br>measures the sum total of all individual layout shift scores for every unexpected layout shift that occurs during the entire lifespan of the page. [Learn more.](https://support.google.com/webmasters/answer/9205520?hl=en) |
| `content` | object | *overall information about content of the page* |
| `plain_text_size` | integer | *total size of the text on the page measured in bytes* |
| `plain_text_rate` | integer | *plaintext rate value*<br>`plain_text_size` to `size` ratio |
| `plain_text_word_count` | float | *number of words on the page* |
| `automated_readability_index` | float | *[Automated Readability Index](https://en.wikipedia.org/wiki/Automated_readability_index)* |
| `coleman_liau_readability_index` | float | *[Coleman–Liau Index](https://en.wikipedia.org/wiki/Coleman%E2%80%93Liau_index)* |
| `dale_chall_readability_index` | float | *[Dale–Chall Readability Index](https://en.wikipedia.org/wiki/Dale%E2%80%93Chall_readability_formula)* |
| `flesch_kincaid_readability_index` | float | *[Flesch–Kincaid Readability Index](https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests)* |
| `smog_readability_index` | float | *[SMOG Readability Index](https://en.wikipedia.org/wiki/SMOG)* |
| `description_to_content_consistency` | float | *consistency of the meta `description` tag with the page content*<br>measured from 0 to 1 |
| `title_to_content_consistency` | float | *consistency of the meta `title` tag with the page content*<br>measured from 0 to 1 |
| `meta_keywords_to_content_consistency` | float | *consistency of meta `keywords`tag with the page content*<br>measured from 0 to 1 |
| `deprecated_tags` | array | *deprecated tags on the page* |
| `duplicate_meta_tags` | array | *duplicate meta tags on the page* |
| `spell` | object | *spellcheck*<br>[hunspell](http://hunspell.github.io/) spellcheck errors |
| `hunspell_language_code` | string | *spellcheck language code* |
| `misspelled` | array | *array of misspelled words* |
| `word` | string | *misspelled word* |
| `resource_errors` | object | *resource errors and warnings* |
| `errors` | array | *resource errors* |
| `line` | integer | *line where the error was found* |
| `message` | string | *text message of the error*<br>the full list of possible HTML errors can be found [here](https://github.com/AngleSharp/AngleSharp/blob/3968eb050e142b1d94550fba407afe772232b126/src/AngleSharp/Html/Parser/HtmlParseError.cs) |
| `warnings` | array | *resource warnings* |
| `line` | integer | *line the warning relates to*<br>note that if `"line": 0`, the warning relates to the whole page |
| `message` | string | *text message of the warning*<br>possible messages:<br>`"Has node with more than 60 childs."` – HTML page has at least 1 tag nesting over 60 tags of the same level<br>`"Has more that 1500 nodes."` – DOM tree contains over 1,500 elements<br>`"HTML depth more than 32 tags."` – DOM depth exceeds 32 nodes |
| `social_media_tags` | object | *object of social media tags found on the page*<br>contains social media tags and their content<br>supported tags include but are not limited to [Open Graph](https://ogp.me/) and [Twitter card](https://developer.twitter.com/en/docs/twitter-for-websites/cards/guides/getting-started) |
| `page_timing` | object | *object of page load metrics* |
| `time_to_interactive` | integer | *[Time To Interactive (TTI)](https://web.dev/interactive/) metric*<br>the time it takes until the user can interact with a page (in milliseconds) |
| `dom_complete` | integer | *time to load resources*<br>the time it takes until the page and all of its subresources are downloaded (in milliseconds) |
| `largest_contentful_paint` | float | *Core Web Vitals metric measuring how fast the largest above-the-fold content element is displayed*<br>The amount of time (in milliseconds) to render the largest content element visible in the viewport, from when the user requests the URL. [Learn more](https://support.google.com/webmasters/answer/9205520?hl=en). |
| `first_input_delay` | float | *Core Web Vitals metric indicating the responsiveness of a page*<br>The time (in milliseconds) from when a user first interacts with your page to the time when the browser responds to that interaction. [Learn more](https://support.google.com/webmasters/answer/9205520?hl=en). |
| `connection_time` | integer | *time to connect to a server*<br>the time it takes until the connection with a server is established (in milliseconds) |
| `time_to_secure_connection` | integer | *time to establish a secure connection*<br>the time it takes until the secure connection with a server is established (in milliseconds) |
| `request_sent_time` | integer | *time to send a request to a server*<br>the time it takes until the request to a server is sent (in milliseconds) |
| `waiting_time` | integer | *time to first byte [(TTFB)](https://en.wikipedia.org/wiki/Time_to_first_byte) in milliseconds* |
| `download_time` | integer | *time it takes for a browser to receive a response (in milliseconds)* |
| `duration_time` | integer | *total time it takes until a browser receives a complete response from a server (in milliseconds)* |
| `fetch_start` | integer | *time to start downloading the HTML resource*<br>the amount of time the browser needs to start downloading a page |
| `fetch_end` | integer | *time to complete downloading the HTML resource*<br>the amount of time the browser needs to complete downloading a page |
| `onpage_score` | float | *shows how page is optimized on a 100-point scale*<br>this field shows how page is optimized considering critical on-page issues and warnings detected;<br>`100` is the highest possible score that means the page does not have any critical on-page issues and important warnings;<br>learn more about how the metric is calculated in [this help center article](https://dataforseo.com/help-center/how-on-page-seo-score-is-calculated) |
| `total_dom_size` | integer | *total [DOM](https://developers.google.com/web/tools/chrome-devtools/dom) size of a page* |
| `custom_js_response` | string/object/integer | *the result of executing a specified JS script*<br>**note** that you should specify a `custom_js` field when [setting a task](https://docs.dataforseo.com/v3/on_page/task_post/) to receive this data and the field type and its value will totally depend on the script you specified;you can also filter the results by this value specifying `filters` in the following way:<br>`["custom_js_response.url", "like", "pixel"]` |
| `custom_js_client_exception` | string | *error when executing a custom js*<br>if the error occurred when executing the script you specified in the `custom_js` field, the error message would be displayed here |
| `broken_resources` | boolean | *indicates whether a page contains broken resources* |
| `broken_links` | boolean | *indicates whether a page contains broken links* |
| `duplicate_title` | boolean | *indicates whether a page has duplicate `title` tags* |
| `duplicate_description` | boolean | *indicates whether a page has a duplicate description* |
| `duplicate_content` | boolean | *indicates whether a page has duplicate content* |
| `click_depth` | integer | *number of clicks it takes to get to the page*<br>indicates the number of clicks from the homepage needed before landing at the target page |
| `size` | integer | *resource size*<br>indicates the size of a given page measured in bytes |
| `encoded_size` | integer | *page size after encoding*<br>indicates the size of the encoded page measured in bytes |
| `total_transfer_size` | integer | *compressed page size*<br>indicates the compressed size of a given page |
| `fetch_time` | string | *date and time when a resource was fetched*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `cache_control` | object | *instructions for caching* |
| `cachable` | boolean | *indicates whether the page is cacheable* |
| `ttl` | integer | *time to live*<br>the amount of time the browser caches a resource |
| `checks` | object | *website checks*<br>on-page check-ups related to the page |
| `no_content_encoding` | boolean | *page with no content encoding*<br>indicates whether a page has no [compression algorithm](http://www.iana.org/assignments/http-parameters/http-parameters.xhtml#content-coding) of the content |
| `high_loading_time` | boolean | *page with high loading time*<br>indicates whether a page loading time exceeds 3 seconds |
| `is_redirect` | boolean | *page with redirects*<br>indicates whether a page has `3XX` redirects to other pages |
| `is_4xx_code` | boolean | *page with `4xx` status codes*<br>indicates whether a page has `4xx` response code |
| `is_5xx_code` | boolean | *page with `5xx` status codes*<br>indicates whether a page has `5xx` response code |
| `is_broken` | boolean | *broken page*<br>indicates whether a page returns a response code less than `200` or greater than `400` |
| `is_www` | boolean | *page with www*<br>indicates whether a page is on a `www` subdomain |
| `is_https` | boolean | *page with the https protocol* |
| `is_http` | boolean | *page with the http protocol* |
| `high_waiting_time` | boolean | *page with high waiting time*<br>indicates whether a page waiting time (aka Time to First Byte) exceeds 1.5 seconds |
| `no_doctype` | boolean | *page with no doctype*<br>indicates whether a page is without the `<!DOCTYPE HTML>` declaration |
| `canonical` | boolean | *page is canonical* |
| `no_encoding_meta_tag` | boolean | *page with no meta tag encoding*<br>indicates whether a page is without `Content-Type`;<br>informative only if the encoding is not explicit in the `Content-Type` header;<br>for example: `Content-Type: "text/html; charset=utf8"`;<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_h1_tag` | boolean | *page with empty or absent h1 tags*<br>**Note:** available for pages with `canonical` check set to `true` |
| `https_to_http_links` | boolean | *HTTPS page has links to HTTP pages*<br>if `true`, this `HTTPS` page has links to `HTTP` pages;<br>**Note:** available for pages with `canonical` check set to `true` |
| `has_html_doctype` | boolean | *page with HTML doctype declaration*<br>if `true`, the page has HTML `DOCTYPE` declaration |
| `size_greater_than_3mb` | boolean | *page with size larger than 3 MB*<br>if `true`, the page size is exceeding 3 MB;<br>**Note:** available for pages with `canonical` check set to `true` |
| `meta_charset_consistency` | boolean | *consistency between charset encoding and page charset*<br>if `true`, the page’s charset encoding doesn’t match the actual charset of the page;<br>**Note:** available for pages with `canonical` check set to `true` |
| `has_meta_refresh_redirect` | boolean | *pages with meta refresh redirect*<br>if `true`, the page has <meta http-equiv=”refresh”> tag that instructs a browser to load another page after a specified time span;<br>**Note:** available for pages with `canonical` check set to `true` |
| `has_render_blocking_resources` | boolean | *page with render-blocking resources*<br>if `true`, the page has render-blocking scripts or stylesheets;<br>**Note:** available for pages with `canonical` check set to `true` |
| `redirect_chain` | boolean | *page with multiple redirects*<br>if `true`, there were at least two redirects before our crawler reached this page |
| `low_content_rate` | boolean | *page with low content rate*<br>indicates whether a page has the `plaintext size` to `page size` ratio of less than 0.1;<br>**Note:** available for pages with `canonical` check set to `true` |
| `high_content_rate` | boolean | *page with high content rate*<br>indicates whether a page has the `plaintext size` to `page size` ratio of more than 0.9;<br>**Note:** available for pages with `canonical` check set to `true` |
| `low_character_count` | boolean | *indicates whether the page has less than 1024 characters*<br>**Note:** available for pages with `canonical` check set to `true` |
| `high_character_count` | boolean | *indicates whether the page has more than 256,000 characters*<br>**Note:** available for pages with `canonical` check set to `true` |
| `small_page_size` | boolean | *indicates whether a page is too small*<br>the value will be `true` if a page size is smaller than 1024 bytes;<br>**Note:** available for pages with `canonical` check set to `true` |
| `large_page_size` | boolean | *indicates whether a page is too heavy*<br>the value will be `true` if a page size exceeds 1 megabyte;<br>**Note:** available for pages with `canonical` check set to `true` |
| `low_readability_rate` | boolean | *page with a low readability rate*<br>indicates whether a page is scored less than 15 points on the [Flesch–Kincaid readability test](https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests);<br>**Note:** available for pages with `canonical` check set to `true` |
| `irrelevant_description` | boolean | *page with irrelevant description*<br>indicates whether a page `description` tag is irrelevant to the content of a page;<br>the relevance threshold is `0.2`;<br>**Note:** available for pages with `canonical` check set to `true` |
| `irrelevant_title` | boolean | *page with irrelevant title*<br>indicates whether a page `title` tag is irrelevant to the content of the page;<br>the relevance threshold is `0.3`;<br>**Note:** available for pages with `canonical` check set to `true` |
| `irrelevant_meta_keywords` | boolean | *page with irrelevant meta keywords*<br>indicates whether a page `keywords` tags are irrelevant to the content of a page;<br>the relevance threshold is `0.6`;<br>**Note:** available for pages with `canonical` check set to `true` |
| `title_too_long` | boolean | *page with a long title*<br>indicates whether the content of the `title` tag exceeds 65 characters;<br>**Note:** available for pages with `canonical` check set to `true` |
| `title_too_short` | boolean | *page with short titles*<br>indicates whether the content of `title` tag is shorter than 30 characters;<br>**Note:** available for pages with `canonical` check set to `true` |
| `deprecated_html_tags` | boolean | *page with deprecated tags*<br>indicates whether a page has [deprecated HTML tags](https://www.codehelp.co.uk/html/deprecated.html);<br>**Note:** available for pages with `canonical` check set to `true` |
| `duplicate_meta_tags` | boolean | *page with duplicate meta tags*<br>indicates whether a page has more than one meta tag of the same type;<br>**Note:** available for pages with `canonical` check set to `true` |
| `duplicate_title_tag` | boolean | *page with more than one title tag*<br>indicates whether a page has more than one `title` tag;<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_image_alt` | boolean | *images without `alt` tags*<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_image_title` | boolean | *images without `title` tags*<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_description` | boolean | *pages with no description*<br>indicates whether a page has an empty or absent `description` meta tag;<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_title` | boolean | *page with no title*<br>indicates whether a page has an empty or absent `title` tag;<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_favicon` | boolean | *page with no favicon*<br>**Note:** available for pages with `canonical` check set to `true` |
| `seo_friendly_url` | boolean | *page with seo-frienldy URL*<br>the ‘SEO-friendliness’ of a page URL is checked by four parameters:<br>– the length of the relative path is less than 120 characters<br>– no special characters<br>– no dynamic parameters<br>– relevance of the URL to the page<br>if at least one of them is failed then such URL is considered as not ‘SEO-friendly’;<br>**Note:** available for pages with `canonical` check set to `true` |
| `flash` | boolean | *page with flash*<br>indicates whether a page has flash elements |
| `frame` | boolean | *page with frames*<br>indicates whether a page contains `frame`, `iframe`, `frameset` tags |
| `lorem_ipsum` | boolean | *page with lorem ipsum*<br>indicates whether a page has *lorem ipsum* content;<br>**Note:** available for pages with `canonical` check set to `true` |
| `has_misspelling` | boolean | *page with misspelled content* |
| `seo_friendly_url_characters_check` | boolean | *URL characters check-up*<br>indicates whether a page URL containing only uppercase and lowercase Latin characters, digits and dashes |
| `seo_friendly_url_dynamic_check` | boolean | *URL dynamic check-up*<br>the value will be `true` if a page has no dynamic parameters in the url |
| `seo_friendly_url_keywords_check` | boolean | *URL keyword check-up*<br>indicates whether a page URL is consistent with the `title` meta tag |
| `seo_friendly_url_relative_length_check` | boolean | *URL length check-up*<br>the value will be `true` if a page URL no longer than 120 characters |
| `is_orphan_page` | boolean | *page with no internal links pointing to it*<br>`true` if the page has no reference from other pages of the domain |
| `is_link_relation_conflict` | boolean | *mix of both followed and nofollowed incoming internal links*<br>`true` if the page receives at least one link with the `rel="nofollow"` attribute and at least one dofollow link |
| `has_links_to_redirects` | boolean | *page is pointing to a page that redirect elsewhere*<br>`true` if the page is pointing to a page that responds with a 3XX redirect |
| `canonical_chain` | boolean | *pages with canonical pointing to a page that has a canonical pointing elsewhere*<br>`true` if the page has a canonical link element pointing to a page that has a canonical pointing to a different page<br>e.g. page a is canonicalized to page b, which is canonicalized to page c |
| `canonical_to_redirect` | boolean | *canonical page pointing to a page that redirects elsewhere*<br>`true` if the page has a canonical link element pointing to a page that responds with a 3XX redirect |
| `canonical_to_broken` | boolean | *canonical link pointing to a broken page*<br>`true` if the page has a a canonical link pointing to a page that responds with a 4xx or 5xx response codes |
| `recursive_canonical` | boolean | *recursive canonical error*<br>`true` if the page contains `rel="canonical"` tag to another page, which in turn, refers back to the initial page |
| `is_orphan_page` | boolean | *page with no internal links pointing to it*<br>`true` if the page has no reference from other pages of the domain |
| `content_encoding` | string | *type of encoding* |
| `media_type` | string | *types of media used to display a page* |
| `server` | string | *server version* |
| `is_resource` | boolean | *indicates whether a page is a single resource* |
| `last_modified` | object | *contains data on changes related to the resource*<br>if there is no data, the value will be `null` |
| `header` | string | *date and time when the header was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| `sitemap` | string | *date and time when the sitemap was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| `meta_tag` | string | *date and time when the meta tag was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Resources
*Source: [https://docs.dataforseo.com/v3/on_page/resources/](https://docs.dataforseo.com/v3/on_page/resources/)*
#### OnPage API Resources

This endpoint will provide you with a list of resources, including images, scripts, stylesheets, and broken elements.
You will get a detailed overview of every resource found on the crawled pages.

If you would like to receive a list of pages that contain a specific resource, please refer to the [Pages By Resource](https://docs.dataforseo.com/v3/on_page/pages_by_resource/) endpoint.

POSThttps://api.dataforseo.com/v3/on_page/resources

Pricing

Your account will not be charged for using this function. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page/onpage-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *ID of the task*<br>**required field**<br>you can get this ID in the response of the [Task POST](https://docs.dataforseo.com/v3/on_page/task_post/) endpoint<br>example:<br>“07131248-1535-0216-1000-17384017ad04” |
| `url` | string | *page URL*<br>optional field<br>specify this field if you want to get the resources for a specific page<br>note that to obtain resource’s `meta` from a particular URL, you should specify the URL in this field;<br>if you do not indicate a `url` when setting a task, resource’s `meta` in the results will be returned based on the data from the page where our crawler first saw the resource |
| `limit` | integer | *the maximum number of returned resources*<br>optional field<br>default value: `100`<br>maximum value: `1000` |
| `offset` | integer | *offset in the results array of returned resources*<br>optional field<br>default value: `0`<br>maximum value: `2000000`<br>if you specify the `10` value, the first ten resources in the results array will be omitted and the data will be provided for the successive resources |
| `filters` | array | *array of results filtering parameters*<br>optional field<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`regex`, `not_regex`, `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`, `like`, `not_like`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>example:<br>`["resource_type","=","stylesheet"]`<br>`[["resource_type","=","image"],<br>"and",["checks.is_https","=",false]]`<br>`[["fetch_timing.duration_time",">",1],"and",[["total_transfer_size",">",100],"or",["checks.high_loading_time","=",true]]]`<br>The full list of possible filters is available [by this link.](https://docs.dataforseo.com/v3/on_page/filters_and_thresholds/?bash) |
| `relevant_pages_filters` | array | *filter the resources by relevant pages*<br>optional field<br>you can use this field to obtain resources from pages matching to the defined parameters<br>you can apply the same filters here as available for the [pages endpoint](https://docs.dataforseo.com/v3/on_page/pages/)<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`regex`, `not_regex`, `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`, `like`, `not_like`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>example:<br>`["checks.no_image_title","=",true]` |
| `order_by` | array | *results sorting rules*<br>optional field<br>you can use the same values as in the `filters` array to sort the results<br>possible sorting types:<br>`asc` – results will be sorted in the ascending order<br>`desc` – results will be sorted in the descending order<br>you should use a comma to set up a sorting type<br>example:<br>`["size,desc"]`<br>**note that you can set no more than three sorting rules in a single request**<br>you should use a comma to separate several sorting rules<br>example:<br>`["size,desc","fetch_timing.fetch_end,desc"]` |
| `search_after_token` | string | *token for subsequent requests*<br>optional field<br>provided in the identical filed of the response to each request;<br>use this parameter to avoid timeouts while trying to obtain over `20,000` results in a single request;<br>by specifying the unique `search_after_token` value from the response array, you will get the subsequent results of the initial task;<br>`search_after_token` values are unique for each subsequent task ;<br>**Note:** if the `search_after_token` is specified in the request, all other parameters should be identical to the previous request |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| ** `result`** | array | *array of results* |
| `crawl_progress` | string | *status of the crawling session*<br>possible values: `in_progress`, `finished` |
| `crawl_status` | object | *details of the crawling session* |
| `max_crawl_pages` | integer | *maximum number of pages to crawl*<br>indicates the `max_crawl_pages` limit you specified when setting a task |
| `pages_in_queue` | integer | *number of pages that are currently in the crawling queue* |
| `pages_crawled` | integer | *number of crawled pages* |
| `total_items_count` | integer | *total number of relevant items crawled*<br> |
| `items_count` | integer | *number of items in the results array*<br> |
| `items` | array | *items array*<br> |
| `resource_type` | string | *type of the returned resource*<br>possible types: `script`, `image`, `stylesheet`, `broken` |
| `meta` | object | *resource properties*<br>the value depends on the `resource_type`<br>note that if you do not indicate a `url` when setting a task, resource’s `meta` is returned based on the data from the page where our crawler first saw the resource;<br>to obtain resource’s `meta` from a particular `url`, specify that URL when setting a task |
| `alternative_text` | string | *content of the image `alt` attribute*<br>the value depends on the `resource_type` |
| `title` | string | *title*<br> |
| `original_width` | integer | *original image width in px*<br> |
| `original_height` | integer | *original image height in px*<br> |
| `width` | integer | *image width in px*<br> |
| `height` | integer | *image height in px*<br> |
| `status_code` | integer | *status code of the page where a given resource is located* |
| `location` | string | *location header*<br>indicates the URL to redirect a page to |
| `url` | string | *resource URL* |
| `size` | integer | *resource size*<br>indicates the size of a given resource measured in bytes |
| `encoded_size` | integer | *resource size after encoding*<br>indicates the size of the encoded resource measured in bytes |
| `total_transfer_size` | integer | *compressed resource size*<br>indicates the compressed size of a given resource in bytes |
| `fetch_time` | string | *date and time when a resource was fetched*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2021-02-17 13:54:15 +00:00` |
| `fetch_timing` | object | *resource fething time range * |
| `duration_time` | integer | *indicates how many milliseconds it took to fetch a resource* |
| `fetch_start` | integer | *time to start downloading the resource*<br>the amount of time a browser needs to start downloading a resource |
| `fetch_end` | integer | *time to complete downloading the resource*<br>the amount of time a browser needs to complete downloading a resource |
| `cache_control` | object | *instructions for caching* |
| `cachable` | boolean | *indicates whether the resource is cacheable* |
| `ttl` | integer | *time to live*<br>the amount of time it takes for the browser to cache a resource; measured in milliseconds |
| `checks` | object | *resource check-ups*<br>contents of the array depend on the `resource_type` |
| `no_content_encoding` | boolean | *resource with no content encoding*<br>indicates whether a page has no [compression algorithm](http://www.iana.org/assignments/http-parameters/http-parameters.xhtml#content-coding) of the content;<br>available for items with the following `resource_type`: `script`, `image`, `stylesheet`, `broken` |
| `high_loading_time` | boolean | *resource with high loading time*<br>indicates whether a resource loading time exceeds 3 seconds;<br>available for items with the following `resource_type`: `script`, `image`, `stylesheet`, `broken` |
| `is_redirect` | boolean | *resource with redirects*<br>indicates whether a page with this resource has `3XX` redirects to other pages;<br>available for items with the following `resource_type`: `script`, `image`, `stylesheet`, `broken` |
| `is_4xx_code` | boolean | *resource with with `4xx` status code*<br>indicates whether a page with this resource has `4XX` response code |
| `is_5xx_code` | boolean | *resource with `5xx` status code*<br>indicates whethera page with this resource has `5XX` response code |
| `is_broken` | boolean | *broken resource*<br>indicates whether a page with this resource returns `4xx`, `5xx` response codes or has broken elements inside the resource;<br>available for items with the following `resource_type`: `script`, `image`, `stylesheet`, `broken` |
| `is_www` | boolean | *page with www*<br>indicates whether a page with this resource is on a `www` subdomain;<br>available for items with the following `resource_type`: `script`, `image`, `stylesheet`, `broken` |
| `is_https` | boolean | *page with the https protocol*<br>available for items with the following `resource_type`: `script`, `image`, `stylesheet`, `broken` |
| `is_http` | boolean | *page with the http protocol*<br>available for items with the following `resource_type`: `script`, `image`, `stylesheet`, `broken` |
| `original_size_displayed` | boolean | *image desplayes in its original size*<br>indicates whether the image is displayed in its original size;<br>available for items with the following `resource_type`: `image` |
| `is_minified` | boolean | *resource is minified*<br>indicates whether the content of a stylesheet or script is minified;<br>available for items with the following `resource_type`: `stylesheet`, `script` |
| `has_redirect` | boolean | *resource has a redirect*<br>available for items with the following `resource_type`: `script`, `image`;<br>if the `resource_type` is `image`, this field will indicate whether other pages and/or resources have redirects pointing at the image;<br>if the `resource_type` is `script`, this field will indicate whether the script contains a redirect |
| `has_subrequests` | boolean | *resource contains subrequests*<br>indicates whether the content of a stylesheet or script contain additional requests;<br>available for items with the following `resource_type`: `stylesheet`, `script` |
| `from_sitemap` | boolean | *resource was found on website’s sitemap<br>if `true`, the resource was found on the sitemap of the website<br>* |
| `resource_errors` | object | *resource errors and warnings* |
| `errors` | array | *resource errors* |
| `line` | integer | *line where the error was found* |
| `column` | integer | *column where the error was found* |
| `message` | string | *text message of the error*<br>the full list of possible HTML errors can be found [here](https://github.com/AngleSharp/AngleSharp/blob/3968eb050e142b1d94550fba407afe772232b126/src/AngleSharp/Html/Parser/HtmlParseError.cs) |
| `status_code` | integer | *status code of the error*<br>possible values:<br>`0` — Unidentified Error;<br>`501` — Html Parse Error;<br>`1501` — JS Parse Error;<br>`2501` — CSS Parse Error;<br>`3501` — Image Parse Error;<br>`3502` — Image Scale Is Zero;<br>`3503` — Image Size Is Zero;<br>`3504` — Image Format Invalid<br> |
| `warnings` | array | *resource warnings* |
| `line` | integer | *line the warning relates to*<br>note that if `"line": 0`, the warning relates to the whole page |
| `column` | integer | *column the warning relates to*<br>note that if `"column": 0`, the warning relates to the whole page |
| `message` | string | *text message of the warning*<br>possible messages:<br>`"Has node with more than 60 childs."` – HTML page has at least 1 tag nesting over 60 tags of the same level<br>`"Has more that 1500 nodes."` – DOM tree contains over 1,500 elements<br>`"HTML depth more than 32 tags."` – DOM depth exceeds 32 nodes |
| `status_code` | integer | *status code of the warning*<br>possible values:<br>`0` — Unidentified Warning;<br>`1` — Has node with more than 60 childs;<br>`2` — Has more that 1500 nodes;<br>`3` — HTML depth more than 32 tags |
| `content_encoding` | string | *type of encoding* |
| `media_type` | string | *types of media used to display a resource* |
| `accept_type` | string | *indicates the expected type of resource*<br>for example, if `"resource_type": "broken"`, `accept_type` will indicate the type of the broken resource<br>possible values:<br>`any`, `none`, `image`, `sitemap`, `robots`, `script`, `stylesheet`, `redirect`, `html`, `text`, `other`, `font` |
| `server` | string | *server version* |
| `last_modified` | object | *contains data on changes related to the resource*<br>if there is no data, the value will be `null` |
| `header` | string | *date and time when the header was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| `sitemap` | string | *date and time when the sitemap was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| `meta_tag` | string | *date and time when the meta tag was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Uncrawlable Resources
*Source: [https://docs.dataforseo.com/v3/on_page/uncrawlable_resources/](https://docs.dataforseo.com/v3/on_page/uncrawlable_resources/)*
#### Uncrawlable Resources

This endpoint returns a list of resources detected on the target website that could not be crawled due to a content type inconsistency. A resource is considered uncrawlable when the content type returned in the server response does not match the content type expected based on how the resource is referenced in the page HTML.

**Note:** only resources that return a `200` HTTP response code are checked.

POSThttps://api.dataforseo.com/v3/on_page/uncrawlable_resources

Pricing

Your account will not be charged for using this function. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page/onpage-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *ID of the task***required field**you can get this ID in the response of the [Task POST](https://docs.dataforseo.com/v3/on_page/task_post/) endpointexample:"07131248-1535-0216-1000-17384017ad04" |
| `limit` | integer | *the maximum number of returned uncrawlable resources*optional fielddefault value: `100`maximum value: `1000` |
| `offset` | integer | *offset in the results array of returned uncrawlable resources*optional fielddefault value: `0` maximum value: `2000000`if you specify the `10` value, the first ten invalid resources in the results array will be omitted and the data will be provided for the successive invalid resources |
| `order_by` | array | *results sorting rules*optional fieldyou can use the same values as in the `filters` array to sort the resultspossible sorting types:`asc` - results will be sorted in the ascending order`desc` - results will be sorted in the descending orderyou should use a comma to set up a sorting typeexample:`["meta.content_type,desc"]`**note that you can set no more than three sorting rules in a single request**you should use a comma to separate several sorting rulesexample:`["meta.content_type,asc","fetch_time,desc"]` |
| `filters` | array | *array of results filtering parameters*optional field**you can add several filters at once (8 filters maximum)**you should set a logical operator `and`, `or` between the conditionsthe following operators are supported:`regex`, `not_regex`, `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`, `like`, `not_like`you can use the `%` operator with `like` and `not_like` to match any string of zero or more charactersexample:` [["meta.content_type","=","image/jpeg"],"and",["url","not_like","%/help-center/%"]]`The full list of possible filters is available [by this link.](https://docs.dataforseo.com/v3/on_page/filters_and_thresholds/?bash) |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `crawl_progress` | string | *status of the crawling session*possible values: `in_progress`, `finished` |
| **`crawl_status`** | object | *details of the crawling session* |
| `max_crawl_pages` | integer | *maximum number of pages to crawl*indicates the `max_crawl_pages` limit you specified when setting a task |
| `pages_in_queue` | integer | *number of pages that are currently in the crawling queue* |
| `pages_crawled` | integer | *number of crawled pages* |
| `total_items_count` | integer | *total number of uncrawlable resources found* total number of uncrawlable resources found during the crawl of the target domain |
| `items_count` | integer | *number of uncrawlable resources in the `items` array* |
| **`items`** | array | *array of uncrawlable resources* |
| `url` | string | *URL of the uncrawlable resource* |
| `reason` | string | *reason the resource is uncrawlable*can take the following values: `content_type_inconsistency` |
| `status_code` | integer | *HTTP response code returned by the uncrawlable resource*possible values: `200` |
| `fetch_time` | string | *date and time when the resource was fetched*in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”example:`2026-03-09 18:20:32 +00:00` |
| **`meta`** | object | *metadata of the uncrawlable resource* |
| `content_type` | string | *actual content type of the resource* |
| `expected_content_types` | array | *expected content types for the resource*list of content types that were expected by the crawler based on how the resource is referenced on the page |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Duplicate Tags
*Source: [https://docs.dataforseo.com/v3/on_page/duplicate_tags/](https://docs.dataforseo.com/v3/on_page/duplicate_tags/)*
#### OnPage API Duplicate Tags

This endpoint returns a list of pages that contain duplicate title or description tags. The response also contains data related to page performance.

POSThttps://api.dataforseo.com/v3/on_page/duplicate_tags

Pricing

Your account will not be charged for using this function. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page/onpage-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *ID of the task*<br>**required field**<br>you can get this ID in the response of the [Task POST](https://docs.dataforseo.com/v3/on_page/task_post/) endpoint<br>example:<br>“07131248-1535-0216-1000-17384017ad04” |
| `type` | string | *duplicate tags type*<br>**required field**<br>indicates the type of duplicate elements found on the pages. The results will depend on the type you specify<br>possible values: `duplicate_title`, `duplicate_description` |
| `accumulator` | string | *tag value*<br>optional field<br>specify a title or description here if you want to receive a list of duplicate pages that contains this tag |
| `limit` | integer | *the maximum number of returned pages*<br>optional field<br>default value: `100`<br>maximum value: `1000` |
| `offset` | integer | *offset in the results array of returned pages*<br>optional field<br>default value: `0`<br>maximum value: `2000000`<br>if you specify the `10` value, the first ten pages in the results array will be omitted and the data will be provided for the successive pages |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| ** `result`** | array | *array of results* |
| `crawl_progress` | string | *status of the crawling session*<br>possible values: `in_progress`, `finished` |
| `crawl_status` | object | *details of the crawling session* |
| `max_crawl_pages` | integer | *maximum number of pages to crawl*<br>indicates the `max_crawl_pages` limit you specified when setting a task |
| `pages_in_queue` | integer | *number of pages that are currently in the crawling queue* |
| `pages_crawled` | integer | *number of crawled pages* |
| `total_pages_count` | integer | *total number of pages with duplicate tags*<br>displays the total number of pages with duplicate tags of the target website |
| `pages_count` | integer | *number of pages with duplicate tags in the response*<br>displays the number of pages with duplicate tags returned in the response |
| `items_count` | integer | *number of items in the results array* |
| `items` | array | *items array* |
| `accumulator` | string | *contains the value of duplicated tag* |
| `total_count` | integer | *total count of duplicate pages* |
| `pages` | array | *pages with duplicate tags* |
| ***‘html’ page*** | | |
| `resource_type` | string | *type of the returned resource = **‘html’*** |
| `status_code` | integer | *status code of the page* |
| `location` | string | *location header*<br>indicates the URL to redirect a page to |
| `url` | string | *page URL* |
| `meta` | object | *page properties*<br>the value depends on the `resource_type` |
| `title` | integer | *page title* |
| `charset` | integer | *[code page](https://en.wikipedia.org/wiki/Code_page)*<br>example: `65001` |
| `follow` | boolean | *indicates whether a page’s ‘meta robots’ allows crawlers to follow the links on the page*<br>if `false`, the page’s ‘meta robots’ tag contains “nofollow” parameter instructing crawlers not to follow the links on the page |
| `generator` | string | *meta tag generator* |
| `htags` | object | *HTML header tags* |
| `description` | string | *content of the meta description tag* |
| `favicon` | string | *favicon of the page* |
| `meta_keywords` | string | *content of the `keywords` meta tag* |
| `canonical` | string | *canonical page* |
| `internal_links_count` | integer | *number of internal links on the page* |
| `external_links_count` | integer | *number of external links on the page* |
| `inbound_links_count` | integer | *number of internal links pointing at the page* |
| `images_count` | integer | *number of images on the page* |
| `images_size` | integer | *total size of images on the page measured in bytes* |
| `scripts_count` | integer | *number of scripts on the page* |
| `scripts_size` | integer | *total size of scripts on the page measured in bytes* |
| `stylesheets_count` | integer | *number of stylesheets on the page* |
| `stylesheets_size` | integer | *total size of stylesheets on the page measured in bytes* |
| `title_length` | integer | *length of the `title` tag in characters* |
| `description_length` | integer | *length of the `description` tag in characters* |
| `render_blocking_scripts_count` | integer | *number of scripts on the page that block page rendering* |
| `render_blocking_stylesheets_count` | integer | *number of CSS styles on the page that block page rendering* |
| `cumulative_layout_shift` | float | *Core Web Vitals metric measuring the layout stability of a page*<br>measures the sum total of all individual layout shift scores for every unexpected layout shift that occurs during the entire lifespan of the page. [Learn more.](https://support.google.com/webmasters/answer/9205520?hl=en) |
| `content` | object | *overall information about content of the page* |
| `plain_text_size` | integer | *total size of the text on the page measured in bytes* |
| `plain_text_rate` | integer | *plaintext rate value*<br>`plain_text_size` to `size` ratio |
| `plain_text_word_count` | float | *number of words on the page* |
| `automated_readability_index` | float | *[Automated Readability Index](https://en.wikipedia.org/wiki/Automated_readability_index)* |
| `coleman_liau_readability_index` | float | *[Coleman–Liau Index](https://en.wikipedia.org/wiki/Coleman%E2%80%93Liau_index)* |
| `dale_chall_readability_index` | float | *[Dale–Chall Readability Index](https://en.wikipedia.org/wiki/Dale%E2%80%93Chall_readability_formula)* |
| `flesch_kincaid_readability_index` | float | *[Flesch–Kincaid Readability Index](https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests)* |
| `smog_readability_index` | float | *[SMOG Readability Index](https://en.wikipedia.org/wiki/SMOG)* |
| `description_to_content_consistency` | float | *consistency of the meta `description` tag with the page content*<br>measured from 0 to 1 |
| `title_to_content_consistency` | float | *consistency of the meta `title` tag with the page content*<br>measured from 0 to 1 |
| `meta_keywords_to_content_consistency` | float | *consistency of meta `keywords`tag with the page content*<br>measured from 0 to 1 |
| `deprecated_tags` | array | *deprecated tags on the page* |
| `duplicate_meta_tags` | array | *duplicate meta tags on the page* |
| `spell` | object | *spellcheck*<br>[hunspell](http://hunspell.github.io/) spellcheck errors |
| `hunspell_language_code` | string | *spellcheck language code* |
| `misspelled` | array | *array of misspelled words* |
| `word` | string | *misspelled word* |
| `resource_errors` | object | *resource errors and warnings* |
| `errors` | array | *resource errors* |
| `line` | integer | *line where the error was found* |
| `message` | string | *text message of the error*<br>the full list of possible HTML errors can be found [here](https://github.com/AngleSharp/AngleSharp/blob/3968eb050e142b1d94550fba407afe772232b126/src/AngleSharp/Html/Parser/HtmlParseError.cs) |
| `warnings` | array | *resource warnings* |
| `line` | integer | *line the warning relates to*<br>note that if `"line": 0`, the warning relates to the whole page |
| `message` | string | *text message of the warning*<br>possible messages:<br>`"Has node with more than 60 childs."` – HTML page has at least 1 tag nesting over 60 tags of the same level<br>`"Has more that 1500 nodes."` – DOM tree contains over 1,500 elements<br>`"HTML depth more than 32 tags."` – DOM depth exceeds 32 nodes |
| `social_media_tags` | object | *object of social media tags found on the page*<br>contains social media tags and their content<br>supported tags include but are not limited to [Open Graph](https://ogp.me/) and [Twitter card](https://developer.twitter.com/en/docs/twitter-for-websites/cards/guides/getting-started) |
| `page_timing` | object | *array of page load metrics* |
| `time_to_interactive` | integer | *[Time To Interactive (TTI)](https://web.dev/interactive/) metric*<br>the time it takes until the user can interact with a page (in milliseconds) |
| `dom_complete` | integer | *time to load resources*<br>the time it takes until the page and all of its subresources are downloaded (in milliseconds) |
| `largest_contentful_paint` | float | *Core Web Vitals metric measuring how fast the largest above-the-fold content element is displayed*<br>The amount of time (in milliseconds) to render the largest content element visible in the viewport, from when the user requests the URL. [Learn more](https://support.google.com/webmasters/answer/9205520?hl=en). |
| `first_input_delay` | float | *Core Web Vitals metric indicating the responsiveness of a page*<br>The time (in milliseconds) from when a user first interacts with your page to the time when the browser responds to that interaction. [Learn more](https://support.google.com/webmasters/answer/9205520?hl=en). |
| `connection_time` | integer | *time to connect to a server*<br>the time it takes until the connection with a server is established (in milliseconds) |
| `time_to_secure_connection` | integer | *time to establish a secure connection*<br>the time it takes until the secure connection with a server is established (in milliseconds) |
| `request_sent_time` | integer | *time to send a request to a server*<br>the time it takes until the request to a server is sent (in milliseconds) |
| `waiting_time` | integer | *time to first byte [(TTFB)](https://en.wikipedia.org/wiki/Time_to_first_byte) in milliseconds* |
| `download_time` | integer | *time it takes for a browser to receive a response (in milliseconds)* |
| `duration_time` | integer | *total time it takes until a browser receives a complete response from a server (in milliseconds)* |
| `fetch_start` | integer | *time to start downloading the HTML resource*<br>the amount of time the browser needs to start downloading a page |
| `fetch_end` | integer | *time to complete downloading the HTML resource*<br>the amount of time the browser needs to complete downloading a page |
| `onpage_score` | float | *shows how page is optimized on a 100-point scale*<br>this field shows how page is optimized considering critical on-page issues and warnings detected;<br>`100` is the highest possible score that means the page does not have any critical on-page issues and important warnings;<br>learn more about how the metric is calculated in [this help center article](https://dataforseo.com/help-center/how-on-page-seo-score-is-calculated) |
| `total_dom_size` | integer | *total [DOM](https://developers.google.com/web/tools/chrome-devtools/dom) size of a page* |
| `custom_js_response` | string/object/integer | *the result of executing a specified JS script*<br>**note** that you should specify a `custom_js` field when [setting a task](https://docs.dataforseo.com/v3/on_page/task_post/) to receive this data and the field type and its value will totally depend on the script you specified; |
| `custom_js_client_exception` | string | *error when executing a custom js*<br>if the error occurred when executing the script you specified in the `custom_js` field, the error message would be displayed here |
| `broken_resources` | boolean | *indicates whether a page contains broken resources* |
| `broken_links` | boolean | *indicates whether a page contains broken links* |
| `duplicate_title` | boolean | *indicates whether a page has duplicate `title` tags* |
| `duplicate_description` | boolean | *indicates whether a page has a duplicate description* |
| `duplicate_content` | boolean | *indicates whether a page has duplicate content* |
| `click_depth` | integer | *number of clicks it takes to get to the page*<br>indicates the number of clicks from the homepage needed before landing at the target page |
| `size` | integer | *resource size*<br>indicates the size of a given page measured in bytes |
| `encoded_size` | integer | *page size after encoding*<br>indicates the size of the encoded page measured in bytes |
| `total_transfer_size` | integer | *compressed page size*<br>indicates the compressed size of a given page |
| `fetch_time` | string | *date and time when a resource was fetched*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `cache_control` | object | *instructions for caching* |
| `cachable` | boolean | *indicates whether the page is cacheable* |
| `ttl` | integer | *time to live*<br>the amount of time the browser caches a resource |
| `checks` | object | *website checks*<br>on-page check-ups related to the page |
| `no_content_encoding` | boolean | *page with no content encoding*<br>indicates whether a page has no [compression algorithm](http://www.iana.org/assignments/http-parameters/http-parameters.xhtml#content-coding) of the content |
| `high_loading_time` | boolean | *page with high loading time*<br>indicates whether a page loading time exceeds 3 seconds |
| `is_redirect` | boolean | *page with redirects*<br>indicates whether a page has `3XX` redirects to other pages |
| `is_4xx_code` | boolean | *page with `4xx` status codes*<br>indicates whether a page has `4xx` response code |
| `is_5xx_code` | boolean | *page with `5xx` status codes*<br>indicates whether a page has `5xx` response code |
| `is_broken` | boolean | *broken page*<br>indicates whether a page returns a response code less than `200` or greater than `400` |
| `is_www` | boolean | *page with www*<br>indicates whether a page is on a `www` subdomain |
| `is_https` | boolean | *page with the https protocol* |
| `is_http` | boolean | *page with the http protocol* |
| `high_waiting_time` | boolean | *page with high waiting time*<br>indicates whether a page waiting time (aka Time to First Byte) exceeds 1.5 seconds |
| `no_doctype` | boolean | *page with no doctype*<br>indicates whether a page is without the `<!DOCTYPE HTML>` declaration |
| `canonical` | boolean | *page is canonical* |
| `no_encoding_meta_tag` | boolean | *page with no meta tag encoding*<br>indicates whether a page is without `Content-Type`<br>informative only if the encoding is not explicit in the `Content-Type` header<br>for example: `Content-Type: "text/html; charset=utf8"`;<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_h1_tag` | boolean | *page with empty or absent h1 tags*<br>**Note:** available for pages with `canonical` check set to `true` |
| `https_to_http_links` | boolean | *HTTPS page has links to HTTP pages*<br>if `true`, this `HTTPS` page has links to `HTTP` pages<br>**Note:** available for pages with `canonical` check set to `true` |
| `has_html_doctype` | boolean | *page with HTML doctype declaration*<br>if `true`, the page has HTML `DOCTYPE` declaration |
| `size_greater_than_3mb` | boolean | *page with size larger than 3 MB*<br>if `true`, the page size is exceeding 3 MB;<br>**Note:** available for pages with `canonical` check set to `true` |
| `meta_charset_consistency` | boolean | *consistency between charset encoding and page charset*<br>if `true`, the page’s charset encoding doesn’t match the actual charset of the page;<br>**Note:** available for pages with `canonical` check set to `true` |
| `has_meta_refresh_redirect` | boolean | *pages with meta refresh redirect*<br>if `true`, the page has <meta http-equiv=”refresh”> tag that instructs a browser to load another page after a specified time span;<br>**Note:** available for pages with `canonical` check set to `true` |
| `has_render_blocking_resources` | boolean | *page with render-blocking resources*<br>if `true`, the page has render-blocking scripts or stylesheets;<br>**Note:** available for pages with `canonical` check set to `true` |
| `redirect_chain` | boolean | *page with multiple redirects*<br>if `true`, there were at least two redirects before our crawler reached this page |
| `low_content_rate` | boolean | *page with low content rate*<br>indicates whether a page has the `plaintext size` to `page size` ratio of less than 0.1;<br>**Note:** available for pages with `canonical` check set to `true` |
| `high_content_rate` | boolean | *page with high content rate*<br>indicates whether a page has the `plaintext size` to `page size` ratio of more than 0.9;<br>**Note:** available for pages with `canonical` check set to `true` |
| `low_character_count` | boolean | *indicates whether the page has less than 1024 characters*<br>**Note:** available for pages with `canonical` check set to `true` |
| `high_character_count` | boolean | *indicates whether the page has more than 256,000 characters*<br>**Note:** available for pages with `canonical` check set to `true` |
| `small_page_size` | boolean | *indicates whether a page is too small*<br>the value will be `true` if a page size is smaller than 1024 bytes;<br>**Note:** available for pages with `canonical` check set to `true` |
| `large_page_size` | boolean | *indicates whether a page is too heavy*<br>the value will be `true` if a page size exceeds 1 megabyte;<br>**Note:** available for pages with `canonical` check set to `true` |
| `low_readability_rate` | boolean | *page with a low readability rate*<br>indicates whether a page is scored less than 15 points on the [Flesch–Kincaid readability test](https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests);<br>**Note:** available for pages with `canonical` check set to `true` |
| `irrelevant_description` | boolean | *page with irrelevant description*<br>indicates whether a page `description` tag is irrelevant to the content of a page;<br>the relevance threshold is `0.2`;<br>**Note:** available for pages with `canonical` check set to `true` |
| `irrelevant_title` | boolean | *page with irrelevant title*<br>indicates whether a page `title` tag is irrelevant to the content of the page;<br>the relevance threshold is `0.3`;<br>**Note:** available for pages with `canonical` check set to `true` |
| `irrelevant_meta_keywords` | boolean | *page with irrelevant meta keywords*<br>indicates whether a page `keywords` tags are irrelevant to the content of a page;<br>the relevance threshold is `0.6`;<br>**Note:** available for pages with `canonical` check set to `true` |
| `title_too_long` | boolean | *page with a long title*<br>indicates whether the content of the `title` tag exceeds 65 characters;<br>**Note:** available for pages with `canonical` check set to `true` |
| `title_too_short` | boolean | *page with short titles*<br>indicates whether the content of `title` tag is shorter than 30 characters;<br>**Note:** available for pages with `canonical` check set to `true` |
| `deprecated_html_tags` | boolean | *page with deprecated tags*<br>indicates whether a page has [deprecated HTML tags](https://www.codehelp.co.uk/html/deprecated.html);<br>**Note:** available for pages with `canonical` check set to `true` |
| `duplicate_meta_tags` | boolean | *page with duplicate meta tags*<br>indicates whether a page has more than one meta tag of the same type;<br>**Note:** available for pages with `canonical` check set to `true` |
| `duplicate_title_tag` | boolean | *page with more than one title tag*<br>indicates whether a page has more than one `title` tag;<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_image_alt` | boolean | *images without `alt` tags*<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_image_title` | boolean | *images without `title` tags*<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_description` | boolean | *pages with no description*<br>indicates whether a page has an empty or absent `description` meta tag;<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_title` | boolean | *page with no title*<br>indicates whether a page has an empty or absent `title` tag;<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_favicon` | boolean | *page with no favicon*<br>**Note:** available for pages with `canonical` check set to `true` |
| `seo_friendly_url` | boolean | *page with seo-frienldy URL*<br>the ‘SEO-friendliness’ of a page URL is checked by four parameters:<br>– the length of the relative path is less than 120 characters<br>– no special characters<br>– no dynamic parameters<br>– relevance of the URL to the page<br>if at least one of them is failed then such URL is considered as not ‘SEO-friendly’<br>**Note:** available for pages with `canonical` check set to `true` |
| `flash` | boolean | *page with flash*<br>indicates whether a page has flash elements |
| `frame` | boolean | *page with frames*<br>indicates whether a page contains `frame`, `iframe`, `frameset` tags |
| `lorem_ipsum` | boolean | *page with lorem ipsum*<br>indicates whether a page has *lorem ipsum* content;<br>**Note:** available for pages with `canonical` check set to `true` |
| `has_misspelling` | boolean | *page with misspelled content* |
| `seo_friendly_url_characters_check` | boolean | *URL characters check-up*<br>indicates whether a page URL containing only uppercase and lowercase Latin characters, digits and dashes |
| `seo_friendly_url_dynamic_check` | boolean | *URL dynamic check-up*<br>the value will be `true` if a page has no dynamic parameters in the url |
| `seo_friendly_url_keywords_check` | boolean | *URL keyword check-up*<br>indicates whether a page URL is consistent with the `title` meta tag |
| `seo_friendly_url_relative_length_check` | boolean | *URL length check-up*<br>the value will be `true` if a page URL no longer than 120 characters |
| `is_orphan_page` | boolean | *page with no internal links pointing to it*<br>`true` if the page has no reference from other pages of the domain |
| `is_link_relation_conflict` | boolean | *mix of both followed and nofollowed incoming internal links*<br>`true` if the page receives at least one link with the `rel="nofollow"` attribute and at least one dofollow link |
| `has_links_to_redirects` | boolean | *page is pointing to a page that redirect elsewhere*<br>`true` if the page is pointing to a page that responds with a 3XX redirect |
| `recursive_canonical` | boolean | *recursive canonical error*<br>`true` if the page contains `rel="canonical"` tag to another page, which in turn, refers back to the initial page |
| `canonical_chain` | boolean | *pages with canonical pointing to a page that has a canonical pointing elsewhere*<br>`true` if the page has a canonical link element pointing to a page that has a canonical pointing to a different page<br>e.g. page a is canonicalized to page b, which is canonicalized to page c |
| `canonical_to_redirect` | boolean | *canonical page pointing to a page that redirect elsewhere*<br>`true` if the page has a canonical link element pointing to a page that responds with a 3XX redirect |
| `canonical_to_broken` | boolean | *canonical link pointing to a broken page*<br>`true` if the page has a a canonical link pointing to a page that responds with a 4xx or 5xx response codes |
| `content_encoding` | string | *type of encoding* |
| `media_type` | string | *types of media used to display a page* |
| `server` | string | *server version* |
| `is_resource` | boolean | *indicates whether a page is a single resource* |
| `last_modified` | object | *contains data on changes related to the resource*<br>if there is no data, the value will be `null` |
| `header` | string | *date and time when the header was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| `sitemap` | string | *date and time when the sitemap was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| `meta_tag` | string | *date and time when the meta tag was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Duplicate Content
*Source: [https://docs.dataforseo.com/v3/on_page/duplicate_content/](https://docs.dataforseo.com/v3/on_page/duplicate_content/)*
#### OnPage API Duplicate Content

This endpoint returns a list of pages that have content similar to the page specified in the request. The response also contains data related to page performance and the similarity index that indicates how similar the compared pages are.

The [SimHash](https://en.wikipedia.org/wiki/SimHash) algorithm is used for calculating the similarity score from 0 to 10, where 0 means that comparative pieces of content are not similar at all, and 10 means they are identical.

POSThttps://api.dataforseo.com/v3/on_page/duplicate_content

Pricing

Your account will not be charged for using this function. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page/onpage-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *ID of the task*<br>**required field**<br>you can get this ID in the response of the [Task POST](https://docs.dataforseo.com/v3/on_page/task_post/) endpoint<br>example:<br>“07131248-1535-0216-1000-17384017ad04” |
| `url` | string | *page URL*<br>**required field**<br>specify the initial page you want to receive duplicate content for |
| `similarity` | integer | *content similarity score*<br>by default, the content is considered duplicate if the value is greater than or equals `6`<br>you can specify any similarity score in the 0-to-10 range |
| `limit` | integer | *the maximum number of returned pages*<br>optional field<br>default value: `100`<br>maximum value: `1000` |
| `offset` | integer | *offset in the results array of returned pages*<br>optional field<br>default value: `0`<br>maximum value: `2000000`<br>if you specify the `10` value, the first ten pages in the results array will be omitted and the data will be provided for the successive pages |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| ** `result`** | array | *array of results* |
| `crawl_progress` | string | *status of the crawling session*<br>possible values: `in_progress`, `finished` |
| `crawl_status` | object | *details of the crawling session* |
| `max_crawl_pages` | integer | *maximum number of pages to crawl*<br>indicates the `max_crawl_pages` limit you specified when setting a task |
| `pages_in_queue` | integer | *number of pages that are currently in the crawling queue* |
| `pages_crawled` | integer | *number of crawled pages* |
| `items_count` | integer | *number of items in the results array* |
| **`items`** | array | *items array* |
| `url` | string | *URL of the specified page* |
| `total_count` | integer | *total count of duplicate pages* |
| `pages` | array | *pages with duplicate content* |
| `similarity` | integer | *content similarity score*<br>by default, the content is considered duplicate if the value is greater than or equals `6`<br>can take values from 0 to 10 |
| `page` | array | *information about the page with duplicate content* |
| ***‘html’ page*** | | |
| `resource_type` | string | *type of the returned resource = **‘html’*** |
| `status_code` | integer | *status code of the page* |
| `location` | string | *location header*<br>indicates the URL to redirect a page to |
| `url` | string | *page URL* |
| `meta` | object | *page properties*<br>the value depends on the `resource_type` |
| `title` | integer | *page title* |
| `charset` | integer | *[code page](https://en.wikipedia.org/wiki/Code_page)*<br>example: `65001` |
| `follow` | boolean | *indicates whether a page’s ‘meta robots’ allows crawlers to follow the links on the page*<br>if `false`, the page’s ‘meta robots’ tag contains “nofollow” parameter instructing crawlers not to follow the links on the page |
| `generator` | string | *meta tag generator* |
| `htags` | object | *HTML header tags* |
| `description` | string | *content of the meta description tag* |
| `favicon` | string | *favicon of the page* |
| `meta_keywords` | string | *content of the `keywords` meta tag* |
| `canonical` | string | *canonical page* |
| `internal_links_count` | integer | *number of internal links on the page* |
| `external_links_count` | integer | *number of external links on the page* |
| `inbound_links_count` | integer | *number of internal links pointing at the page* |
| `images_count` | integer | *number of images on the page* |
| `images_size` | integer | *total size of images on the page measured in bytes* |
| `scripts_count` | integer | *number of scripts on the page* |
| `scripts_size` | integer | *total size of scripts on the page measured in bytes* |
| `stylesheets_count` | integer | *number of stylesheets on the page* |
| `stylesheets_size` | integer | *total size of stylesheets on the page measured in bytes* |
| `title_length` | integer | *length of the `title` tag in characters* |
| `description_length` | integer | *length of the `description` tag in characters* |
| `render_blocking_scripts_count` | integer | *number of scripts on the page that block page rendering* |
| `render_blocking_stylesheets_count` | integer | *number of CSS styles on the page that block page rendering* |
| `cumulative_layout_shift` | float | *Core Web Vitals metric measuring the layout stability of a page*<br>measures the sum total of all individual layout shift scores for every unexpected layout shift that occurs during the entire lifespan of the page. [Learn more.](https://support.google.com/webmasters/answer/9205520?hl=en) |
| `content` | object | *overall information about content of the page* |
| `plain_text_size` | integer | *total size of the text on the page measured in bytes* |
| `plain_text_rate` | integer | *plaintext rate value*<br>`plain_text_size` to `size` ratio |
| `plain_text_word_count` | float | *number of words on the page* |
| `automated_readability_index` | float | *[Automated Readability Index](https://en.wikipedia.org/wiki/Automated_readability_index)* |
| `coleman_liau_readability_index` | float | *[Coleman–Liau Index](https://en.wikipedia.org/wiki/Coleman%E2%80%93Liau_index)* |
| `dale_chall_readability_index` | float | *[Dale–Chall Readability Index](https://en.wikipedia.org/wiki/Dale%E2%80%93Chall_readability_formula)* |
| `flesch_kincaid_readability_index` | float | *[Flesch–Kincaid Readability Index](https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests)* |
| `smog_readability_index` | float | *[SMOG Readability Index](https://en.wikipedia.org/wiki/SMOG)* |
| `description_to_content_consistency` | float | *consistency of the meta `description` tag with the page content*<br>measured from 0 to 1 |
| `title_to_content_consistency` | float | *consistency of the meta `title` tag with the page content*<br>measured from 0 to 1 |
| `meta_keywords_to_content_consistency` | float | *consistency of meta `keywords`tag with the page content*<br>measured from 0 to 1 |
| `deprecated_tags` | array | *deprecated tags on the page* |
| `duplicate_meta_tags` | array | *duplicate meta tags on the page* |
| `spell` | object | *spellcheck*<br>[hunspell](http://hunspell.github.io/) spellcheck errors |
| `hunspell_language_code` | string | *spellcheck language code* |
| `misspelled` | array | *array of misspelled words* |
| `word` | string | *misspelled word* |
| `resource_errors` | object | *resource errors and warnings* |
| `errors` | array | *resource errors* |
| `line` | integer | *line where the error was found* |
| `message` | string | *text message of the error*<br>the full list of possible HTML errors can be found [here](https://github.com/AngleSharp/AngleSharp/blob/3968eb050e142b1d94550fba407afe772232b126/src/AngleSharp/Html/Parser/HtmlParseError.cs) |
| `warnings` | array | *resource warnings* |
| `line` | integer | *line the warning relates to*<br>note that if `"line": 0`, the warning relates to the whole page |
| `message` | string | *text message of the warning*<br>possible messages:<br>`"Has node with more than 60 childs."` – HTML page has at least 1 tag nesting over 60 tags of the same level<br>`"Has more that 1500 nodes."` – DOM tree contains over 1,500 elements<br>`"HTML depth more than 32 tags."` – DOM depth exceeds 32 nodes |
| `social_media_tags` | object | *array of social media tags found on the page*<br>contains social media tags and their content<br>supported tags include but are not limited to [Open Graph](https://ogp.me/) and [Twitter card](https://developer.twitter.com/en/docs/twitter-for-websites/cards/guides/getting-started) |
| `page_timing` | object | *object of page load metrics* |
| `time_to_interactive` | integer | *[Time To Interactive (TTI)](https://web.dev/interactive/) metric*<br>the time it takes until the user can interact with a page (in milliseconds) |
| `dom_complete` | integer | *time to load resources*<br>the time it takes until the page and all of its subresources are downloaded (in milliseconds) |
| `largest_contentful_paint` | float | *Core Web Vitals metric measuring how fast the largest above-the-fold content element is displayed*<br>The amount of time (in milliseconds) to render the largest content element visible in the viewport, from when the user requests the URL. [Learn more](https://support.google.com/webmasters/answer/9205520?hl=en). |
| `first_input_delay` | float | *Core Web Vitals metric indicating the responsiveness of a page*<br>The time (in milliseconds) from when a user first interacts with your page to the time when the browser responds to that interaction. [Learn more](https://support.google.com/webmasters/answer/9205520?hl=en). |
| `connection_time` | integer | *time to connect to a server*<br>the time it takes until the connection with a server is established (in milliseconds) |
| `time_to_secure_connection` | integer | *time to establish a secure connection*<br>the time it takes until the secure connection with a server is established (in milliseconds) |
| `request_sent_time` | integer | *time to send a request to a server*<br>the time it takes until the request to a server is sent (in milliseconds) |
| `waiting_time` | integer | *time to first byte [(TTFB)](https://en.wikipedia.org/wiki/Time_to_first_byte) in milliseconds* |
| `download_time` | integer | *time it takes for a browser to receive a response (in milliseconds)* |
| `duration_time` | integer | *total time it takes until a browser receives a complete response from a server (in milliseconds)* |
| `fetch_start` | integer | *time to start downloading the HTML resource*<br>the amount of time the browser needs to start downloading a page |
| `fetch_end` | integer | *time to complete downloading the HTML resource*<br>the amount of time the browser needs to complete downloading a page |
| `onpage_score` | float | *shows how page is optimized on a 100-point scale*<br>this field shows how page is optimized considering critical on-page issues and warnings detected;<br>`100` is the highest possible score that means the page does not have any critical on-page issues and important warnings;<br>learn more about how the metric is calculated in [this help center article](https://dataforseo.com/help-center/how-on-page-seo-score-is-calculated) |
| `total_dom_size` | integer | *total [DOM](https://developers.google.com/web/tools/chrome-devtools/dom) size of a page* |
| `custom_js_response` | string/object/integer | *the result of executing a specified JS script*<br>**note** that you should specify a `custom_js` field when [setting a task](https://docs.dataforseo.com/v3/on_page/task_post/) to receive this data and the field type and its value will totally depend on the script you specified;you can also filter the results by this value specifying `filters` in the following way:<br>`["custom_js_response.url", "like", "pixel"]` |
| `custom_js_client_exception` | string | *error when executing a custom js*<br>if the error occurred when executing the script you specified in the `custom_js` field, the error message would be displayed here |
| `broken_resources` | boolean | *indicates whether a page contains broken resources* |
| `broken_links` | boolean | *indicates whether a page contains broken links* |
| `duplicate_title` | boolean | *indicates whether a page has duplicate `title` tags* |
| `duplicate_description` | boolean | *indicates whether a page has a duplicate description* |
| `duplicate_content` | boolean | *indicates whether a page has duplicate content* |
| `click_depth` | integer | *number of clicks it takes to get to the page*<br>indicates the number of clicks from the homepage needed before landing at the target page |
| `size` | integer | *resource size*<br>indicates the size of a given page measured in bytes |
| `encoded_size` | integer | *page size after encoding*<br>indicates the size of the encoded page measured in bytes |
| `total_transfer_size` | integer | *compressed page size*<br>indicates the compressed size of a given page |
| `fetch_time` | string | *date and time when a resource was fetched*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `cache_control` | object | *instructions for caching* |
| `cachable` | boolean | *indicates whether the page is cacheable* |
| `ttl` | integer | *time to live*<br>the amount of time the browser caches a resource |
| `checks` | object | *website checks*<br>on-page check-ups related to the page |
| `no_content_encoding` | boolean | *page with no content encoding*<br>indicates whether a page has no [compression algorithm](http://www.iana.org/assignments/http-parameters/http-parameters.xhtml#content-coding) of the content |
| `high_loading_time` | boolean | *page with high loading time*<br>indicates whether a page loading time exceeds 3 seconds |
| `is_redirect` | boolean | *page with redirects*<br>indicates whether a page has `3XX` redirects to other pages |
| `is_4xx_code` | boolean | *page with `4xx` status codes*<br>indicates whether a page has `4xx` response code |
| `is_5xx_code` | boolean | *page with `5xx` status codes*<br>indicates whether a page has `5xx` response code |
| `is_broken` | boolean | *broken page*<br>indicates whether a page returns a response code less than `200` or greater than `400` |
| `is_www` | boolean | *page with www*<br>indicates whether a page is on a `www` subdomain |
| `is_https` | boolean | *page with the https protocol* |
| `is_http` | boolean | *page with the http protocol* |
| `high_waiting_time` | boolean | *page with high waiting time*<br>indicates whether a page waiting time (aka Time to First Byte) exceeds 1.5 seconds |
| `no_doctype` | boolean | *page with no doctype*<br>indicates whether a page is without the `<!DOCTYPE HTML>` declaration |
| `canonical` | boolean | *page is canonical* |
| `no_encoding_meta_tag` | boolean | *page with no meta tag encoding*<br>indicates whether a page is without `Content-Type`;<br>informative only if the encoding is not explicit in the `Content-Type` header;<br>for example: `Content-Type: "text/html; charset=utf8"`;<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_h1_tag` | boolean | *page with empty or absent h1 tags*<br>**Note:** available for pages with `canonical` check set to `true` |
| `https_to_http_links` | boolean | *HTTPS page has links to HTTP pages*<br>if `true`, this `HTTPS` page has links to `HTTP` pages<br>**Note:** available for pages with `canonical` check set to `true` |
| `has_html_doctype` | boolean | *page with HTML doctype declaration*<br>if `true`, the page has HTML `DOCTYPE` declaration |
| `size_greater_than_3mb` | boolean | *page with size larger than 3 MB*<br>if `true`, the page size is exceeding 3 MB;<br>**Note:** available for pages with `canonical` check set to `true` |
| `meta_charset_consistency` | boolean | *consistency between charset encoding and page charset*<br>if `true`, the page’s charset encoding doesn’t match the actual charset of the page;<br>**Note:** available for pages with `canonical` check set to `true` |
| `has_meta_refresh_redirect` | boolean | *pages with meta refresh redirect*<br>if `true`, the page has <meta http-equiv=”refresh”> tag that instructs a browser to load another page after a specified time span;<br>**Note:** available for pages with `canonical` check set to `true` |
| `has_render_blocking_resources` | boolean | *page with render-blocking resources*<br>if `true`, the page has render-blocking scripts or stylesheets;<br>**Note:** available for pages with `canonical` check set to `true` |
| `redirect_chain` | boolean | *page with multiple redirects*<br>if `true`, there were at least two redirects before our crawler reached this page |
| `low_content_rate` | boolean | *page with low content rate*<br>indicates whether a page has the `plaintext size` to `page size` ratio of less than 0.1;<br>**Note:** available for pages with `canonical` check set to `true` |
| `high_content_rate` | boolean | *page with high content rate*<br>indicates whether a page has the `plaintext size` to `page size` ratio of more than 0.9;<br>**Note:** available for pages with `canonical` check set to `true` |
| `low_character_count` | boolean | *indicates whether the page has less than 1024 characters*<br>**Note:** available for pages with `canonical` check set to `true` |
| `high_character_count` | boolean | *indicates whether the page has more than 256,000 characters*<br>**Note:** available for pages with `canonical` check set to `true` |
| `small_page_size` | boolean | *indicates whether a page is too small*<br>the value will be `true` if a page size is smaller than 1024 bytes;<br>**Note:** available for pages with `canonical` check set to `true` |
| `large_page_size` | boolean | *indicates whether a page is too heavy*<br>the value will be `true` if a page size exceeds 1 megabyte;<br>**Note:** available for pages with `canonical` check set to `true` |
| `low_readability_rate` | boolean | *page with a low readability rate*<br>indicates whether a page is scored less than 15 points on the [Flesch–Kincaid readability test](https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests);<br>**Note:** available for pages with `canonical` check set to `true` |
| `irrelevant_description` | boolean | *page with irrelevant description*<br>indicates whether a page `description` tag is irrelevant to the content of a page;<br>the relevance threshold is `0.2;`<br>**Note:** available for pages with `canonical` check set to `true` |
| `irrelevant_title` | boolean | *page with irrelevant title*<br>indicates whether a page `title` tag is irrelevant to the content of the page<br>the relevance threshold is `0.3`<br>**Note:** available for pages with `canonical` check set to `true` |
| `irrelevant_meta_keywords` | boolean | *page with irrelevant meta keywords*<br>indicates whether a page `keywords` tags are irrelevant to the content of a page<br>the relevance threshold is `0.6`<br>**Note:** available for pages with `canonical` check set to `true` |
| `title_too_long` | boolean | *page with a long title*<br>indicates whether the content of the `title` tag exceeds 65 characters;<br>**Note:** available for pages with `canonical` check set to `true` |
| `title_too_short` | boolean | *page with short titles*<br>indicates whether the content of `title` tag is shorter than 30 characters;<br>**Note:** available for pages with `canonical` check set to `true` |
| `deprecated_html_tags` | boolean | *page with deprecated tags*<br>indicates whether a page has [deprecated HTML tags](https://www.codehelp.co.uk/html/deprecated.html);<br>**Note:** available for pages with `canonical` check set to `true` |
| `duplicate_meta_tags` | boolean | *page with duplicate meta tags*<br>indicates whether a page has more than one meta tag of the same type;<br>**Note:** available for pages with `canonical` check set to `true` |
| `duplicate_title_tag` | boolean | *page with more than one title tag*<br>indicates whether a page has more than one `title` tag;<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_image_alt` | boolean | *images without `alt` tags*<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_image_title` | boolean | *images without `title` tags*<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_description` | boolean | *pages with no description*<br>indicates whether a page has an empty or absent `description` meta tag;<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_title` | boolean | *page with no title*<br>indicates whether a page has an empty or absent `title` tag;<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_favicon` | boolean | *page with no favicon*<br>**Note:** available for pages with `canonical` check set to `true` |
| `seo_friendly_url` | boolean | *page with seo-frienldy URL*<br>the ‘SEO-friendliness’ of a page URL is checked by four parameters:<br>– the length of the relative path is less than 120 characters<br>– no special characters<br>– no dynamic parameters<br>– relevance of the URL to the page<br>if at least one of them is failed then such URL is considered as not ‘SEO-friendly’;<br>**Note:** available for pages with `canonical` check set to `true` |
| `flash` | boolean | *page with flash*<br>indicates whether a page has flash elements |
| `frame` | boolean | *page with frames*<br>indicates whether a page contains `frame`, `iframe`, `frameset` tags |
| `lorem_ipsum` | boolean | *page with lorem ipsum*<br>indicates whether a page has *lorem ipsum* content;<br>**Note:** available for pages with `canonical` check set to `true` |
| `has_misspelling` | boolean | *page with misspelled content* |
| `seo_friendly_url_characters_check` | boolean | *URL characters check-up*<br>indicates whether a page URL containing only uppercase and lowercase Latin characters, digits and dashes |
| `seo_friendly_url_dynamic_check` | boolean | *URL dynamic check-up*<br>the value will be `true` if a page has no dynamic parameters in the url |
| `seo_friendly_url_keywords_check` | boolean | *URL keyword check-up*<br>indicates whether a page URL is consistent with the `title` meta tag |
| `seo_friendly_url_relative_length_check` | boolean | *URL length check-up*<br>the value will be `true` if a page URL no longer than 120 characters |
| `is_orphan_page` | boolean | *page with no internal links pointing to it*<br>`true` if the page has no reference from other pages of the domain |
| `is_link_relation_conflict` | boolean | *mix of both followed and nofollowed incoming internal links*<br>`true` if the page receives at least one link with the `rel="nofollow"` attribute and at least one dofollow link |
| `has_links_to_redirects` | boolean | *page is pointing to a page that redirect elsewhere*<br>`true` if the page is pointing to a page that responds with a 3XX redirect |
| `recursive_canonical` | boolean | *recursive canonical error*<br>`true` if the page contains `rel="canonical"` tag to another page, which in turn, refers back to the initial page |
| `canonical_chain` | boolean | *pages with canonical pointing to a page that has a canonical pointing elsewhere*<br>`true` if the page has a canonical link element pointing to a page that has a canonical pointing to a different page<br>e.g. page a is canonicalized to page b, which is canonicalized to page c |
| `canonical_to_redirect` | boolean | *canonical page pointing to a page that redirect elsewhere*<br>`true` if the page has a canonical link element pointing to a page that responds with a 3XX redirect |
| `canonical_to_broken` | boolean | *canonical link pointing to a broken page*<br>`true` if the page has a a canonical link pointing to a page that responds with a 4xx or 5xx response codes |
| `content_encoding` | string | *type of encoding* |
| `media_type` | string | *types of media used to display a page* |
| `server` | string | *server version* |
| `is_resource` | boolean | *indicates whether a page is a single resource* |
| `last_modified` | object | *contains data on changes related to the resource*<br>if there is no data, the value will be `null` |
| `header` | string | *date and time when the header was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| `sitemap` | string | *date and time when the sitemap was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| `meta_tag` | string | *date and time when the meta tag was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Links
*Source: [https://docs.dataforseo.com/v3/on_page/links/](https://docs.dataforseo.com/v3/on_page/links/)*
#### Links

This endpoint will provide you with a list of internal and external links detected on a target website.
The following link types are supported:
`anchor` – links that point to a specific portion of a webpage;
`image` – links that point to an image;
`canonical` – links that point to a canonical page;
`meta` – links with `meta http-equiv=refresh` ;
`alternate` – links with `link rel="alternate"` pointing to an alternative version of a webpage ;
`redirect` – links with redirect status.

POSThttps://api.dataforseo.com/v3/on_page/links

Pricing

Your account will not be charged for using this function. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page/onpage-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *ID of the task*<br>**required field**<br>you can get this ID in the response of the [Task POST](https://docs.dataforseo.com/v3/on_page/task_post/) endpoint<br>example:<br>“07131248-1535-0216-1000-17384017ad04” |
| `page_from` | string | *relative page URL*<br>optional field<br>if you use this field, the API response will contain only links from the specified page<br>note that in this field you can specify relative URLs only |
| `page_to` | string | *relative page URL*<br>optional field<br>if you use this field, the API response will contain only internal links pointing to the specified page<br>note that in this field you can specify relative URLs only |
| `limit` | integer | *the maximum number of returned links*<br>optional field<br>default value: `100`<br>maximum value: `1000` |
| `offset` | integer | *offset in the results array of returned links*<br>optional field<br>default value: `0`<br>maximum value: `2000000`<br>if you specify the `10` value, the first ten links in the results array will be omitted and the data will be provided for the successive links |
| `filters` | array | *array of results filtering parameters*<br>optional field<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`regex`, `not_regex`, `=`, `<>`, `in`, `not_in`, `like`, `not_like`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>example:<br>`["direction","=","external"]`<br>`[["domain_to","<>","example.com"],<br>"and",<br>["link_from","not_like","%example.com/blog%"]]`<br>`[["direction","=","external"],<br>"and",<br>[["link_from","like","%example.com/blog%"],"or",["link_from","like","%example.com/help%"]]]`<br>The full list of possible filters is available [by this link.](https://docs.dataforseo.com/v3/on_page/filters_and_thresholds/?bash) |
| `search_after_token` | string | *token for subsequent requests*<br>optional field<br>provided in the identical filed of the response to each request;<br>use this parameter to avoid timeouts while trying to obtain over `20,000` results in a single request;<br>by specifying the unique `search_after_token` value from the response array, you will get the subsequent results of the initial task;<br>`search_after_token` values are unique for each subsequent task ;<br>**Note:** if the `search_after_token` is specified in the request, all other parameters should be identical to the previous request |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| ** `result`** | array | *array of results* |
| `crawl_progress` | string | *status of the crawling session*<br>possible values: `in_progress`, `finished` |
| `crawl_status` | object | *details of the crawling session* |
| `max_crawl_pages` | integer | *maximum number of pages to crawl*<br>indicates the `max_crawl_pages` limit you specified when setting a task |
| `pages_in_queue` | integer | *number of pages that are currently in the crawling queue* |
| `pages_crawled` | integer | *number of crawled pages* |
| `total_items_count` | integer | *total number of relevant items in the database*<br> |
| `items_count` | integer | *number of items in the results array*<br> |
| **`items`** | array | *items array*<br> |
| **anchor link** | | |
| `type` | string | *type of the link = **‘anchor’***<br><a> tag |
| `domain_from` | string | *referring domain*<br>the link was found on this domain |
| `domain_to` | string | *referenced domain*<br>the link is pointing to this domain |
| `page_from` | string | *referring page*<br>relative URL of the page on which the link was found |
| `page_to` | string | *referenced page*<br>relative URL of the page to which the link is pointing |
| `link_from` | string | *referring page*<br>absolute URL of the page on which the link was found |
| `link_to` | string | *referenced page*<br>absolute URL of the page to which the link is pointing |
| `link_attribute` | array | *link attribute added to external link*<br>indicates link attributes added to the `link_to` on the `page_from`<br>example:<br>`["ugc","noopener"]` |
| `dofollow` | boolean | *indicates whether the link is dofollow*<br>if the value is `true`, the link doesn’t have a `rel="nofollow"` attribute |
| `page_from_scheme` | string | *[url scheme](https://en.wikipedia.org/wiki/List_of_URI_schemes) of the referring page* |
| `page_to_scheme` | string | *[url scheme](https://en.wikipedia.org/wiki/List_of_URI_schemes) of the referenced page*<br> |
| `direction` | string | *direction of the link*<br>possible values: `internal`, `external` |
| `is_broken` | boolean | *link is broken*<br>indicates whether a link is directing to a broken page or resource |
| `text` | string | *anchor text* |
| `is_link_relation_conflict` | boolean | *indicates that the link may have a conflict with another link*<br>if `true`, at least one link pointing to `link_to` has a `rel="nofollow"` attribute **and** at least one is dofollow |
| `page_to_status_code` | integer | *status code of the referenced page*<br>status code of the page to which the link is pointing |
| **image link** | | |
| `type` | string | *type of the link = **‘image’***<br><img> tag contained in the <a> tag |
| `domain_from` | string | *referring domain*<br>the link was found on this domain |
| `domain_to` | string | *referenced domain*<br>the link is pointing to this domain |
| `page_from` | string | *referring page*<br>relative URL of the page on which the link was found |
| `page_to` | string | *referenced page*<br>relative URL of the page to which the link is pointing |
| `link_from` | string | *referring page*<br>absolute URL of the page on which the link was found |
| `link_to` | string | *referenced page*<br>absolute URL of the page to which the link is pointing |
| `link_attribute` | array | *link attribute added to external link*<br>indicates link attributes added to the `link_to` on the `page_from`<br>`["ugc","noopener"]` |
| `dofollow` | boolean | *indicates whether the link is dofollow*<br>if the value is `true`, the link doesn’t have a `rel="nofollow"` attribute |
| `page_from_scheme` | string | *[url scheme](https://en.wikipedia.org/wiki/List_of_URI_schemes) of the referring page* |
| `page_to_scheme` | string | *[url scheme](https://en.wikipedia.org/wiki/List_of_URI_schemes) of the referenced page*<br> |
| `direction` | string | *direction of the link*<br>possible values: `internal`, `external` |
| `is_broken` | boolean | *link is broken*<br>indicates whether a link is directing to a broken page or resource |
| `text` | string | *image text* |
| `image_alt` | string | *alternative text for the image* |
| `image_src` | string | *url of the image* |
| `is_link_relation_conflict` | boolean | *indicates that the link may have a conflict with another link*<br>if `true`, at least one link pointing to `link_to` has a `rel="nofollow"` attribute **and** at least one is dofollow |
| `page_to_status_code` | integer | *status code of the referenced page*<br>status code of the page to which the link is pointing |
| **link tag link** | | |
| `type` | string | *type of the link = **‘link’***<br><link> tag |
| `domain_from` | string | *referring domain*<br>the link was found on this domain |
| `domain_to` | string | *referenced domain*<br>the link is pointing to this domain |
| `page_from` | string | *referring page*<br>relative URL of the page on which the link was found |
| `page_to` | string | *referenced page*<br>relative URL of the page to which the link is pointing |
| `link_from` | string | *referring page*<br>absolute URL of the page on which the link was found |
| `link_to` | string | *referenced page*<br>absolute URL of the page to which the link is pointing |
| `dofollow` | boolean | *indicates whether the link is dofollow*<br>if the value is `true`, the link doesn’t have a `rel="nofollow"` attribute |
| `page_from_scheme` | string | *[url scheme](https://en.wikipedia.org/wiki/List_of_URI_schemes) of the referring page* |
| `page_to_scheme` | string | *[url scheme](https://en.wikipedia.org/wiki/List_of_URI_schemes) of the referenced page*<br> |
| `direction` | string | *direction of the link*<br>possible values: `internal`, `external` |
| `is_broken` | boolean | *link is broken*<br>indicates whether a link is directing to a broken page or resource |
| `is_link_relation_conflict` | boolean | *indicates that the link may have a conflict with another link*<br>if `true`, at least one link pointing to `link_to` has a `rel="nofollow"` attribute **and** at least one is dofollow |
| `page_to_status_code` | integer | *status code of the referenced page*<br>status code of the page to which the link is pointing |
| **canonical link** | | |
| `type` | string | *type of the link = **‘canonical’***<br><meta rel=”canonical”> tag<br> |
| `domain_from` | string | *referring domain*<br>the link was found on this domain |
| `domain_to` | string | *referenced domain*<br>the link is pointing to this domain |
| `page_from` | string | *referring page*<br>relative URL of the page on which the link was found |
| `page_to` | string | *referenced page*<br>relative URL of the page to which the link is pointing |
| `link_from` | string | *referring page*<br>absolute URL of the page on which the link was found |
| `link_to` | string | *referenced page*<br>absolute URL of the page to which the link is pointing |
| `dofollow` | boolean | *indicates whether the link is dofollow*<br>if the value is `true`, the link doesn’t have a `rel="nofollow"` attribute |
| `page_from_scheme` | string | *[url scheme](https://en.wikipedia.org/wiki/List_of_URI_schemes) of the referring page* |
| `page_to_scheme` | string | *[url scheme](https://en.wikipedia.org/wiki/List_of_URI_schemes) of the referenced page*<br> |
| `direction` | string | *direction of the link*<br>possible values: `internal`, `external` |
| `is_broken` | boolean | *link is broken*<br>indicates whether a link is directing to a broken page or resource |
| `is_link_relation_conflict` | boolean | *indicates that the link may have a conflict with another link*<br>if `true`, at least one link pointing to `link_to` has a `rel="nofollow"` attribute **and** at least one is dofollow |
| `page_to_status_code` | integer | *status code of the referenced page*<br>status code of the page to which the link is pointing |
| **meta link** | | |
| `type` | string | *type of the link = **‘meta’***<br><meta http-equiv=”refresh” content=”X;url=https://wikipedia.org”> tag<br> |
| `domain_from` | string | *referring domain*<br>the link was found on this domain |
| `domain_to` | string | *referenced domain*<br>the link is pointing to this domain |
| `page_from` | string | *referring page*<br>relative URL of the page on which the link was found |
| `page_to` | string | *referenced page*<br>relative URL of the page to which the link is pointing |
| `link_from` | string | *referring page*<br>absolute URL of the page on which the link was found |
| `link_to` | string | *referenced page*<br>absolute URL of the page to which the link is pointing |
| `dofollow` | boolean | *indicates whether the link is dofollow*<br>if the value is `true`, the link doesn’t have a `rel="nofollow"` attribute |
| `page_from_scheme` | string | *[url scheme](https://en.wikipedia.org/wiki/List_of_URI_schemes) of the referring page* |
| `page_to_scheme` | string | *[url scheme](https://en.wikipedia.org/wiki/List_of_URI_schemes) of the referenced page*<br> |
| `direction` | string | *direction of the link*<br>possible values: `internal`, `external` |
| `is_broken` | boolean | *link is broken*<br>indicates whether a link is directing to a broken page or resource |
| `is_link_relation_conflict` | boolean | *indicates that the link may have a conflict with another link*<br>if `true`, at least one link pointing to `link_to` has a `rel="nofollow"` attribute **and** at least one is dofollow |
| `page_to_status_code` | integer | *status code of the referenced page*<br>status code of the page to which the link is pointing |
| **alternate link** | | |
| `type` | string | *type of the link = **‘alternate’***<br><link rel=”alternate”> tag<br> |
| `is_valid_hreflang` | boolean | *hreflang validity status*<br>indicates whether the hreflang attribute is correctly implemented |
| `hreflang` | string | *hreflang attribute value*<br>language and optional country code specified in the hreflang attribute<br>example: `"en-US"`, `"fr"` |
| `domain_from` | string | *referring domain*<br>the link was found on this domain |
| `domain_to` | string | *referenced domain*<br>the link is pointing to this domain |
| `page_from` | string | *referring page*<br>relative URL of the page on which the link was found |
| `page_to` | string | *referenced page*<br>relative URL of the page to which the link is pointing |
| `link_from` | string | *referring page*<br>absolute URL of the page on which the link was found |
| `link_to` | string | *referenced page*<br>absolute URL of the page to which the link is pointing |
| `dofollow` | boolean | *indicates whether the link is dofollow*<br>if the value is `true`, the link doesn’t have a `rel="nofollow"` attribute |
| `page_from_scheme` | string | *[url scheme](https://en.wikipedia.org/wiki/List_of_URI_schemes) of the referring page* |
| `page_to_scheme` | string | *[url scheme](https://en.wikipedia.org/wiki/List_of_URI_schemes) of the referenced page*<br> |
| `direction` | string | *direction of the link*<br>possible values: `internal`, `external` |
| `is_broken` | boolean | *link is broken*<br>indicates whether a link is directing to a broken page or resource |
| `is_link_relation_conflict` | boolean | *indicates that the link may have a conflict with another link*<br>if `true`, at least one link pointing to `link_to` has a `rel="nofollow"` attribute **and** at least one is dofollow |
| `page_to_status_code` | integer | *status code of the referenced page*<br>status code of the page to which the link is pointing |
| **redirect link** | | |
| `type` | string | *type of the link = **‘redirect’***<br>HTTP redirect with 3xx status code |
| `domain_from` | string | *referring domain*<br>the link was found on this domain |
| `domain_to` | string | *referenced domain*<br>the link is pointing to this domain |
| `page_from` | string | *referring page*<br>relative URL of the page on which the link was found |
| `page_to` | string | *referenced page*<br>relative URL of the page to which the link is pointing |
| `link_from` | string | *referring page*<br>absolute URL of the page on which the link was found |
| `link_to` | string | *referenced page*<br>absolute URL of the page to which the link is pointing |
| `dofollow` | boolean | *indicates whether the link is dofollow*<br>if the value is `true`, the link doesn’t have a `rel="nofollow"` attribute |
| `page_from_scheme` | string | *[url scheme](https://en.wikipedia.org/wiki/List_of_URI_schemes) of the referring page* |
| `page_to_scheme` | string | *[url scheme](https://en.wikipedia.org/wiki/List_of_URI_schemes) of the referenced page*<br> |
| `direction` | string | *direction of the link*<br>possible values: `internal`, `external` |
| `is_broken` | boolean | *link is broken*<br>indicates whether a link is directing to a broken page or resource |
| `is_link_relation_conflict` | boolean | *indicates that the link may have a conflict with another link*<br>if `true`, at least one link pointing to `link_to` has a `rel="nofollow"` attribute **and** at least one is dofollow |
| `page_to_status_code` | integer | *status code of the referenced page*<br>status code of the page to which the link is pointing |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Redirect Chains
*Source: [https://docs.dataforseo.com/v3/on_page/redirect_chains/](https://docs.dataforseo.com/v3/on_page/redirect_chains/)*
#### Redirect Сhains

Redirect chains occur when there are at least two redirects between the initial URL and the destination URL. For example, if page A redirects to page B which redirects to page C, such a series of redirects is considered a redirect chain. Sometimes, if page B redirects back to page A, the redirect chain becomes closed and is considered a redirect loop.

This endpoint will provide you with a full list of redirect URLs that form redirect chains. Using the Redirect Сhains endpoint, you’ll be able to quickly identify and trace down multiple redirects issues.

POSThttps://api.dataforseo.com/v3/on_page/redirect_chains

Pricing

Your account will not be charged for using this function. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page/onpage-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *ID of the task*<br>**required field**<br>you can get this ID in the response of the [Task POST](https://docs.dataforseo.com/v3/on_page/task_post/) endpoint<br>example:<br>“07131248-1535-0216-1000-17384017ad04” |
| `url` | string | *page URL*<br>optional field<br>absolute URL of the target page<br>if you use this field, the API response will return only redirect chains which contain the specified URL |
| `limit` | integer | *the maximum number of returned redirect chains*<br>optional field<br>default value: `100`<br>maximum value: `1000` |
| `offset` | integer | *offset in the results array of returned redirect chains*<br>optional field<br>default value: `0`<br>maximum value: `2000000`<br>if you specify the `10` value, the first ten redirect chains in the results array will be omitted and the data will be provided for the successive redirect chains |
| `filters` | array | *array of results filtering parameters*<br>optional field<br>**you can use only one filtering parameter with this endpoint**<br>the following filtering parameter is supported:<br>`is_redirect_loop`<br>the following operators are supported:<br>`regex`, `not_regex`, `=`, `<>`<br>examples:<br>`["is_redirect_loop","=","true"]`<br>`["is_redirect_loop","<>","false"]` |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| ** `result`** | array | *array of results* |
| `crawl_progress` | string | *status of the crawling session*<br>possible values: `in_progress`, `finished` |
| `crawl_status` | object | *details of the crawling session* |
| `max_crawl_pages` | integer | *maximum number of pages to crawl*<br>indicates the `max_crawl_pages` limit you specified when setting a task |
| `pages_in_queue` | integer | *number of pages that are currently in the crawling queue* |
| `pages_crawled` | integer | *number of crawled pages* |
| `total_items_count` | integer | *total number of relevant items in the database* |
| `items_count` | integer | *number of items in the results array* |
| **`items`** | array | *items array* |
| `is_redirect_loop` | bool | *indicates if redirects in `chain` start and end at the same URL*<br>if `true`, the last URL from the chain redirects back to the original URL |
| **`chain`** | array | *contains links that form a chain* |
| `type` | string | *type of the link = **‘redirect’***<br>HTTP redirect with 3xx status code |
| `domain_from` | string | *referring domain*<br>the link was found on this domain |
| `domain_to` | string | *referenced domain*<br>the link is pointing to this domain |
| `page_from` | string | *referring page*<br>relative URL of the page on which the link was found |
| `page_to` | string | *referenced page*<br>relative URL of the page to which the link is pointing |
| `link_from` | string | *referring page*<br>absolute URL of the page on which the link was found |
| `link_to` | string | *referenced page*<br>absolute URL of the page to which the link is pointing |
| `dofollow` | boolean | *indicates whether the link is dofollow*<br>if the value is `true`, the link doesn’t have a `rel="nofollow"` attribute |
| `page_from_scheme` | string | *[url scheme](https://en.wikipedia.org/wiki/List_of_URI_schemes) of the referring page* |
| `page_to_scheme` | string | *[url scheme](https://en.wikipedia.org/wiki/List_of_URI_schemes) of the referenced page* |
| `direction` | string | *direction of the link*<br>possible values: `internal`, `external` |
| `is_broken` | boolean | *link is broken*<br>indicates whether a link is directing to a broken page or resource |
| `is_link_relation_conflict` | boolean | *indicates that the link may have a conflict with another link*<br>if `true`, at least one link pointing to the URL in `link_to` has a `rel="nofollow"` attribute **and** at least one is dofollow |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Non-Indexable
*Source: [https://docs.dataforseo.com/v3/on_page/non_indexable/](https://docs.dataforseo.com/v3/on_page/non_indexable/)*
#### OnPage API Non-indexable Pages

This endpoint returns a list of pages that are blocked from being indexed by Google and other search engines through `robots.txt`, HTTP headers, or meta tags settings.

POSThttps://api.dataforseo.com/v3/on_page/non_indexable

Pricing

Your account will not be charged for using this function. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page/onpage-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *ID of the task*<br>**required field**<br>you can get this ID in the response of the [Task POST](https://docs.dataforseo.com/v3/on_page/task_post/) endpoint<br>example:<br>“07131248-1535-0216-1000-17384017ad04” |
| `limit` | integer | *the maximum number of returned pages*<br>optional field<br>default value: `100`<br>maximum value: `1000` |
| `offset` | integer | *offset in the results array of returned pages*<br>optional field<br>default value: `0`<br>maximum value: `2000000`<br>if you specify the `10` value, the first ten pages in the results array will be omitted and the data will be provided for the successive pages |
| `filters` | array | *array of results filtering parameters*<br>optional field<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`regex`, `not_regex`, `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`, `like`, `not_like`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>example:<br>`["reason","=","robots_txt"]``[["reason","<>","robots_txt"],<br>"and",<br>["url","not_like","%/wp-admin/%"]]`<br>`[["url","not_like","%/wp-admin/%"],<br>"and",<br>[["reason","<>","meta_tag"],"or",["reason","<>","http_header"]]]`<br>The full list of possible filters is available [by this link.](https://docs.dataforseo.com/v3/on_page/filters_and_thresholds/?bash) |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| ** `result`** | array | *array of results* |
| `crawl_progress` | string | *status of the crawling session*<br>possible values: `in_progress`, `finished` |
| `crawl_status` | object | *details of the crawling session* |
| `max_crawl_pages` | integer | *maximum number of pages to crawl*<br>indicates the `max_crawl_pages` limit you specified when setting a task |
| `pages_in_queue` | integer | *number of pages that are currently in the crawling queue* |
| `pages_crawled` | integer | *number of crawled pages* |
| `total_items_count` | integer | *total number of relevant items in the database*<br> |
| `items_count` | integer | *number of items in the results array*<br> |
| `items` | array | *items array*<br> |
| `reason` | string | *the reason why the page is non-indexable*<br>can take the following values: `robots_txt`, `meta_tag`, `http_header`, `attribute`, `too_many_redirects` |
| `url` | string | *url of the non-indexable page* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Waterfall
*Source: [https://docs.dataforseo.com/v3/on_page/waterfall/](https://docs.dataforseo.com/v3/on_page/waterfall/)*
#### OnPage API Waterfall

This endpoint is designed to provide you with the page speed insights. Using this function you can get detailed information about the page loading time, time to secure connection, the time it takes to load page resources, and so on.

This feature is especially useful for creating page speed tests and other tools for checking website performance.

POSThttps://api.dataforseo.com/v3/on_page/waterfall

Pricing

Your account will not be charged for using this function. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page/onpage-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *ID of the task*<br>**required field**<br>you can get this ID in the response of the [Task POST](https://docs.dataforseo.com/v3/on_page/task_post/) endpoint<br>example:<br>“07131248-1535-0216-1000-17384017ad04” |
| `url` | string | *page URL*<br>**required field**<br>specify the pages you want to receive timing for |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| ** `result`** | array | *array of results* |
| `crawl_progress` | string | *status of the crawling session*<br>possible values: `in_progress`, `finished` |
| `crawl_status` | object | *details of the crawling session* |
| `max_crawl_pages` | integer | *maximum number of pages to crawl*<br>indicates the `max_crawl_pages` limit you specified when setting a task |
| `pages_in_queue` | integer | *number of pages that are currently in the crawling queue* |
| `pages_crawled` | integer | *number of crawled pages* |
| `items_count` | integer | *number of items in the results array*<br> |
| `items` | array | *items array*<br> |
| `page_url` | string | *URL of the page* |
| `time_to_interactive` | integer | *[Time To Interactive (TTI)](https://web.dev/interactive/) metric*<br>the time it takes until the user can interact with a page (in milliseconds) |
| `dom_complete` | integer | *time to load resources*<br>the time it takes until the page and all of its subresources are downloaded (in milliseconds) |
| `connection_time` | integer | *time to connect to a server*<br>the time it takes until the connection with a server is established (in milliseconds) |
| `time_to_secure_connection` | integer | *time to establish a secure connection*<br>the time it takes until the secure connection with a server is established (in milliseconds) |
| `request_sent_time` | integer | *time to send a request to a server*<br>the time it takes until the request to a server is sent (in milliseconds) |
| `waiting_time` | integer | *time to first byte [(TTFB)](https://en.wikipedia.org/wiki/Time_to_first_byte) in milliseconds* |
| `download_time` | integer | *time it takes for a browser to receive a response (in milliseconds)* |
| `duration_time` | integer | *total time it takes until a browser receives a complete response from a server (in milliseconds)*<br> |
| `fetch_start` | integer | *time to start downloading the HTML resource*<br>the amount of time the browser needs to start downloading a page |
| `fetch_end` | integer | *time to complete downloading the HTML resource*<br>the amount of time the browser needs to complete downloading a page |
| `resources` | array | *resource-specific timing*<br>contains separate arrays with timing for each resource found on the page |
| `resource_type` | string | *type of the returned resource* |
| `url` | string | *resource URL* |
| `initiator` | string | *resource initiator* |
| `duration_time` | integer | *total time it takes until a browser receives a complete response from a server (in milliseconds)* |
| `fetch_start` | integer | *time to start downloading the resource*<br>the amount of time the browser needs to start downloading a resource |
| `fetch_end` | integer | *time to complete downloading the resource*<br>the amount of time the browser needs to complete downloading a resource |
| `location` | object | *location of the resource in the document*<br>parameters defining the location of the specific resource within the document’s HTML |
| `line` | integer | *line number*<br>the number of the line on which the resource is located |
| `offset_left` | integer | *position in line*<br>the number of line characters before the resource;<br>sometimes referred to as *column*<br>**Note:** counts from 1, i.e. if the resource doesn’t have any characters to the left, the value will be 1 |
| `offset_top` | integer | *position in the document*<br>the total number of characters between the resource and the top of HTML |
| `is_render_blocking` | boolean | *indicates whether the resource blocks rendering*<br> |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Keyword Density
*Source: [https://docs.dataforseo.com/v3/on_page/keyword_density/](https://docs.dataforseo.com/v3/on_page/keyword_density/)*
#### Keyword Density

This endpoint will provide you with keyword density and keyword frequency data for terms appearing on the specified website or web page. You can filter and sort the data that will be retrieved with this API call.

**Note:** to use this endpoint, make sure the `calculate_keyword_density` parameter in the [Task Post](https://docs.dataforseo.com/v3/on_page/task_post/) request is set to `true`

POSThttps://api.dataforseo.com/v3/on_page/keyword_density

Pricing

Your account will not be charged for using this function. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page/onpage-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *ID of the task*<br>**required field**<br>you can get this ID in the response of the [Task POST](https://docs.dataforseo.com/v3/on_page/task_post/) endpoint<br>example:<br>“07131248-1535-0216-1000-17384017ad04” |
| `keyword_length` | integer | *number of words for a keyword*<br>**required field**<br>possible values:<br>`1`, `2`, `3`, `4`, `5` |
| `url` | string | *page URL*<br>optional field<br>**if you do not specify a page here, the results will be provided for the whole website**<br>if you use this field, the API response will contain only keywords from the specified page<br>a page should be specified with absolute URL (including `http://` or `https://`) |
| `limit` | integer | *the maximum number of returned keywords*<br>optional field<br>default value: `100`<br>maximum value: `1000` |
| `filters` | array | *array of results filtering parameters*<br>optional field<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`regex`, `not_regex`, `=`, `<>`, `in`, `not_in`, `like`, `not_like`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>example:<br>`["keyword","=","%seo%"]`<br>`[["keyword","=","%seo%"],<br>"and",<br>["frequency","<","6"]]`<br>`[["keyword","not_like","%seo%"],<br>"and",<br>[["frequency",">","6"],"or",["density",">","0.02"]]]`<br>The full list of possible filters is available [by this link.](https://docs.dataforseo.com/v3/on_page/filters_and_thresholds/?bash) |
| `order_by` | array | *results sorting rules*<br>optional field<br>you can use the same values as in the `filters` array to sort the results<br>possible sorting types:<br>`asc` – results will be sorted in the ascending order<br>`desc` – results will be sorted in the descending order<br>you should use a comma to set up a sorting type<br>example:<br>`["frequency,desc"]`<br>**note that you can set no more than three sorting rules in a single request**<br>you should use a comma to separate several sorting rules<br>example:<br>`["keyword,asc","frequency,desc"]` |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| ** `result`** | array | *array of results* |
| `crawl_progress` | string | *status of the crawling session*<br>possible values: `in_progress`, `finished` |
| `crawl_status` | object | *details of the crawling session* |
| `max_crawl_pages` | integer | *maximum number of pages to crawl*<br>indicates the `max_crawl_pages` limit you specified when setting a task |
| `pages_in_queue` | integer | *number of pages that are currently in the crawling queue* |
| `pages_crawled` | integer | *number of crawled pages* |
| `total_items_count` | integer | *total number of relevant items*<br>total number of keywords on the specified website or web page matching the set `keyword_length` and `filters` |
| `items_count` | integer | *number of items in the results array*<br> |
| **`items`** | array | *items array*<br> |
| `keyword` | string | *returned keyword* |
| `frequency` | integer | *keyword frequency*<br>number of times the keyword appears on the website (or webpage if you specified a `url`) |
| `density` | integer | *keyword density*<br>calculated as a ratio of `frequency` to the total count of keywords with the set `keyword_length` on the web page or website |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Microdata
*Source: [https://docs.dataforseo.com/v3/on_page/microdata/](https://docs.dataforseo.com/v3/on_page/microdata/)*
#### OnPage API Microdata

This endpoint is designed to validate structured JSON-LD data and Microdata. Using this function you will obtain microdata available on the specified page of the target website and detailed results of its validation.
To use this endpoint, set the `validate_micromarkup` parameter to `true` in the [POST request](https://docs.dataforseo.com/v3/on_page/task_post/) to OnPage API.

POSThttps://api.dataforseo.com/v3/on_page/microdata

Pricing

Your account will not be charged for using this function. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page/onpage-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *ID of the task*<br>**required field**<br>you can get this ID in the response of the [Task POST](https://docs.dataforseo.com/v3/on_page/task_post/) endpoint<br>example:<br>`"07131248-1535-0216-1000-17384017ad04"` |
| `url` | string | *resource URL*<br>**required field**<br>you can get this URL in the response of the [Pages](https://docs.dataforseo.com/v3/on_page/pages/) endpoint<br>example:<br>`https://dataforseo.com/apis` |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| ** `result`** | array | *array of results* |
| `crawl_progress` | string | *status of the crawling session*<br>possible values: `in_progress`, `finished` |
| `crawl_status` | object | *details of the crawling session* |
| `max_crawl_pages` | integer | *maximum number of pages to crawl*<br>indicates the `max_crawl_pages` limit you specified when setting a task |
| `pages_in_queue` | integer | *number of pages that are currently in the crawling queue* |
| `pages_crawled` | integer | *number of crawled pages* |
| `test_summary` | object | *microdata validation test results* |
| `fatal` | integer | *number of fatal microdata errors* |
| `error` | integer | *number of serious microdata errors* |
| `warning` | integer | *number of microdata warnings* |
| `info` | integer | *number of microdata information flags* |
| `items_count` | integer | *number of items in the results array*<br> |
| `items` | array | *items array*<br> |
| ***‘json_ld’*** | | |
| `type` | string | *type of the item = **‘json_ld’*** |
| `inspection_info` | object | *information related to microdata validation* |
| `types` | array | *parent microdata types*<br>for a full list of available types, please visit [schema.org](https://schema.org/docs/full.html) |
| `fields` | array | *microdata fields*<br>an array of objects containing data fields related to the certain microdata type |
| `name` | string | *field name*<br>name of the data field |
| `types` | array | *list of microdata sub-types* |
| `value` | array | *microdata value*<br>microdata value specified on a target web page |
| `test_results` | object | *microdata validation test results*<br>sub-type microdata test results that contain detected errors and related messages |
| `level` | string | *level of microdata error*<br>can take the following values: `fatal`, `error`, `warning`, `info` |
| `message` | string | *message associated with an error*<br>message providing the details of the detected error |
| `fields` | array | *microdata fields*<br>an array of objects containing data fields related to the certain microdata type |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Raw HTML
*Source: [https://docs.dataforseo.com/v3/on_page/raw_html/](https://docs.dataforseo.com/v3/on_page/raw_html/)*
#### OnPage API Raw HTML

This endpoint returns the HTML of a page you indicate in the request.

**Note:** to use this endpoint, make sure the `store_raw_html` parameter in the [Task Post](https://docs.dataforseo.com/v3/on_page/task_post/) request is set to `true`

POSThttps://api.dataforseo.com/v3/on_page/raw_html

Pricing

Your account will not be charged for using this function. You can get the results of the task within the next 7 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page/onpage-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *ID of the task*<br>**required field**<br>you can get this ID in the response of the [Task POST](https://docs.dataforseo.com/v3/on_page/task_post/) endpoint<br>example:<br>“07131248-1535-0216-1000-17384017ad04” |
| `url` | string | *page url*<br>**required field**<br>the absolute URL of a page to request HTML<br>**Note:** this field is optional if the task was set using the [Instant Pages endpoint](https://docs.dataforseo.com/v3/on_page/instant_pages/) |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| ** `result`** | array | *array of results* |
| `crawl_progress` | string | *status of the crawling session*<br>possible values: `in_progress`, `finished` |
| `crawl_status` | object | *details of the crawling session* |
| `max_crawl_pages` | integer | *maximum number of pages to crawl*<br>indicates the `max_crawl_pages` limit you specified when setting a task |
| `pages_in_queue` | integer | *number of pages that are currently in the crawling queue* |
| `pages_crawled` | integer | *number of crawled pages* |
| `items_count` | integer | *number of items in the results array*<br> |
| `items` | object | *items object*<br> |
| `html` | string | *HTML **page* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Page Screenshot
*Source: [https://docs.dataforseo.com/v3/on_page/page_screenshot/](https://docs.dataforseo.com/v3/on_page/page_screenshot/)*
#### OnPage API Page Screenshot

Using this endpoint, you can capture a full high-quality screenshot of any webpage. In this way, you can review the target page as the DataForSEO crawler and Googlebot see it.

Your account will be charged per each page screenshot.

POSThttps://api.dataforseo.com/v3/on_page/page_screenshot

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page/onpage-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**You can send up to 2000 API requests per minute, with each request containing no more than 20 tasks. The maximum number of simultaneous requests you can send is limited to 30.**

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `url` | string | *page url*<br>**required field**<br>absolute URL of the page to snap<br>**note:** if the URL you indicate here returns a 404 status code or the indicated value is not a valid URL, you will obtain `"error_message":"Screenshot is empty"` in the response array |
| `accept_language` | string | *language header for accessing the website*<br>optional field<br>all locale formats are supported (xx, xx-XX, xxx-XX, etc.)<br>**note:** if you do not specify this parameter, some websites may deny access; in this case, you will obtain `"error_message":"Screenshot is empty"` in the response array |
| `custom_user_agent` | string | *custom user agent*<br>optional field<br>custom user agent for crawling a website<br>example: `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36<br>`<br>default value: `Mozilla/5.0 (compatible; RSiteAuditor)` |
| `browser_preset` | string | *preset for browser screen parameters*<br>optional field<br>if you use this field, you don’t need to indicate `browser_screen_width`, `browser_screen_height`, `browser_screen_scale_factor`<br>possible values:<br>`desktop`, `mobile`, `tablet`<br>`desktop` preset will apply the following values:<br>`browser_screen_width: 1920`<br>`browser_screen_height: 1080`<br>`browser_screen_scale_factor: 1`<br>`mobile` preset will apply the following values:<br>`browser_screen_width: 390`<br>`browser_screen_height: 844`<br>`browser_screen_scale_factor: 3`<br>`tablet` preset will apply the following values:<br>`browser_screen_width: 1024`<br>`browser_screen_height: 1366`<br>`browser_screen_scale_factor: 2`<br>**Note:** in this endpoint, the `enable_browser_rendering`, `enable_javascript`, `load_resources`, and `enable_xhr` parameters are always enabled. |
| `browser_screen_width` | integer | *browser screen width*<br>optional field<br>you can set a custom browser screen width to perform audit for a particular device;<br>if you use this field, you don’t need to indicate `browser_preset` as it will be ignored;<br>minimum value, in pixels: `240`<br>maximum value, in pixels: `9999` |
| `browser_screen_height` | integer | *browser screen height*<br>optional field<br>you can set a custom browser screen height to perform audit for a particular device;<br>if you use this field, you don’t need to indicate `browser_preset` as it will be ignored;<br>minimum value, in pixels: `240`<br>maximum value, in pixels: `9999` |
| `browser_screen_scale_factor` | float | *browser screen scale factor*<br>optional field<br>you can set a custom browser screen resolution ratio to perform audit for a particular device;<br>if you use this field, you don’t need to indicate `browser_preset` as it will be ignored;<br>minimum value: `0.5`<br>maximum value: `3` |
| `full_page_screenshot` | boolean | *take a screenshot of the full page*<br>optional field<br>set to `false` if you want to capture only the part of the page displayed before scrolling<br>default value: `true` |
| `disable_cookie_popup` | boolean | *disable the cookie popup *<br>optional field<br>set to `true` if you want to disable the popup requesting cookie consent from the user;<br>default value:<br>`false`<br> |
| `switch_pool` | boolean | *switch proxy pool*<br>optional field<br>if `true`, additional proxy pools will be used to obtain the requested data;<br>the parameter can be used if a multitude of tasks is set simultaneously, resulting in occasional `rate-limit` and/or `site_unreachable` errors |
| `ip_pool_for_scan` | string | *proxy pool*<br>optional field<br>you can choose a location of the proxy pool that will be used to obtain the requested data;<br>the parameter can be used if page content is inaccessible in one of the locations, resulting in occasional `site_unreachable` errors<br>possible values: `us`, `de`<br> |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| ** `result`** | array | *array of results* |
| `crawl_progress` | string | *status of the crawling session*<br>possible values: `in_progress`, `finished` |
| `error_message` | string | *error message*<br>if the `url` you indicated returns a 404 status code or is not a valid URL, you will obtain `"error_message":"Screenshot is empty"`<br>if no error is encountered, the value will be `null` |
| `items_count` | integer | *number of items in the results array*<br> |
| `items` | array | *items array*<br> |
| `image` | string | *screenshot of the requested page*<br>URL of the page screenshot on the DataForSEO storage |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Content Parsing
*Source: [https://docs.dataforseo.com/v3/on_page/content_parsing/](https://docs.dataforseo.com/v3/on_page/content_parsing/)*
#### OnPage API Content Parsing

This endpoint allows parsing the content on any page you specify and will return the structured content of the target page, including link URLs, anchors, headings, and textual content.

Note: to use this endpoint, make sure the `enable_content_parsing` parameter in the [Task Post request](https://docs.dataforseo.com/v3/on_page-task_post/) is set to `true`.

POSThttps://api.dataforseo.com/v3/on_page/content_parsing

Pricing

Your account will not be charged for using this function. You can get the results of the task within the next 30 days for free. The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page/onpage-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `url` | string | *URL of the content to parse*<br>**required field**<br>URL of the page to parse<br>example:<br>`https://dataforseo.com/blog/a-versatile-alternative-to-google-trends-exploring-the-power-of-dataforseo-trends-api` |
| `id` | string | *ID of the task*<br>**required field**<br>you can get this ID in the response of the [Task POST](https://docs.dataforseo.com/v3/on_page/task_post/) endpoint<br>**note:** the `enable_content_parsing` parameter in the POST request must be set to `true`<br>example:<br>`"07131248-1535-0216-1000-17384017ad04"` |
| `markdown_view` | boolean | *return page content as markdown*<br>optional field<br>if set to `true`, the markdown-formatted content of the page will be returned in the `page_as_markdown` field of the response;<br>default value: `false` |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the response array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| ** `result`** | array | *array of results* |
| `crawl_progress` | string | *status of the crawling session*<br>possible values: `in_progress`, `finished` |
| `crawl_status` | object | *details of the crawling session* |
| `items_count` | integer | *number of items in the results array*<br> |
| `items` | array | *items array*<br> |
| ***‘сontent_parsing_element’*** | | |
| `type` | string | *type of the returned item = **‘сontent_parsing_element’*** |
| `fetch_time` | string | *date and time when the content was fethced*<br>example:<br>`"2022-11-01 10:02:52 +00:00"` |
| `status_code` | integer | *status code of the page* |
| `page_content` | object | *parsed content of the page*<br> |
| `header` | object | *parsed content of the header*<br> |
| `primary_content` | array | *primary content on the page*<br>you can find more information about content priority calculation in this [help center article](https://dataforseo.com/help-center/difference-between-primary-and-secondary-content)<br> |
| `text` | string | *content text*<br> |
| `url` | string | * page URL*<br>displayed in case the text is a link anchor<br> |
| `urls` | array | contains other URLs and anchors found in the content element<br> |
| `url` | string | other URL found in the content element<br> |
| `anchor_text` | string | text of the URL’s anchor<br> |
| `secondary_content` | array | *secondary content on the page*<br>you can find more information about content priority calculation in this [help center article](https://dataforseo.com/help-center/difference-between-primary-and-secondary-content)<br> |
| `text` | string | *content text*<br> |
| `url` | string | * page URL*<br>displayed in case the text is a link anchor<br> |
| `urls` | array | contains other URLs and anchors found in the content element<br> |
| `url` | string | other URL found in the content element<br> |
| `anchor_text` | string | text of the URL’s anchor<br> |
| `table_content` | array | *content of the table on the page*<br> |
| `header` | array | *content of the header of the table*<br> |
| `row_cells` | array | *content of the row cells of the header*<br> |
| `text` | string | *text in the row cell*<br> |
| `urls` | array | *contains other URLs and anchors found in the cell*<br> |
| `url` | string | *URL found in the cell*<br> |
| `anchor_text` | string | *text of the URL’s anchor*<br> |
| `is_header` | boolean | *indicates if the text belongs to the header*<br> |
| `body` | array | *content of the body of the table*<br> |
| `row_cells` | array | *content of the row cells of the header*<br> |
| `text` | string | *text in the row cell*<br> |
| `urls` | array | *contains other URLs and anchors found in the cell*<br> |
| `url` | string | *URL found in the cell*<br> |
| `anchor_text` | string | *text of the URL’s anchor*<br> |
| `is_header` | boolean | *indicates if the text belongs to the header*<br> |
| `footer` | array | *content of the footer of the table*<br> |
| `row_cells` | array | *content of the row cells of the header*<br> |
| `text` | string | *text in the row cell*<br> |
| `urls` | array | *contains other URLs and anchors found in the cell*<br> |
| `url` | string | *URL found in the cell*<br> |
| `anchor_text` | string | *text of the URL’s anchor*<br> |
| `is_header` | boolean | *indicates if the text belongs to the header*<br> |
| `footer` | object | *parsed content of the footer*<br> |
| `primary_content` | array | *primary content on the page*<br>you can find more information about content priority calculation in this [help center article](https://dataforseo.com/help-center/difference-between-primary-and-secondary-content)<br> |
| `text` | string | *content text*<br> |
| `url` | string | * page URL*<br>displayed in case the text is a link anchor<br> |
| `urls` | array | contains other URLs and anchors found in the content element<br> |
| `url` | string | other URL found in the content element<br> |
| `anchor_text` | string | text of the URL’s anchor<br> |
| `secondary_content` | array | *secondary content on the page*<br>you can find more information about content priority calculation in this [help center article](https://dataforseo.com/help-center/difference-between-primary-and-secondary-content)<br> |
| `text` | string | *content text*<br> |
| `url` | string | * page URL*<br>displayed in case the text is a link anchor<br> |
| `urls` | array | contains other URLs and anchors found in the content element<br> |
| `url` | string | other URL found in the content element<br> |
| `anchor_text` | string | text of the URL’s anchor<br> |
| `table_content` | array | *content of the table on the page*<br> |
| `header` | array | *content of the header of the table*<br> |
| `row_cells` | array | *content of the row cells of the header*<br> |
| `text` | string | *text in the row cell*<br> |
| `urls` | array | *contains other URLs and anchors found in the cell*<br> |
| `url` | string | *URL found in the cell*<br> |
| `anchor_text` | string | *text of the URL’s anchor*<br> |
| `is_header` | boolean | *indicates if the text belongs to the header*<br> |
| `body` | array | *content of the body of the table*<br> |
| `row_cells` | array | *content of the row cells of the header*<br> |
| `text` | string | *text in the row cell*<br> |
| `urls` | array | *contains other URLs and anchors found in the cell*<br> |
| `url` | string | *URL found in the cell*<br> |
| `anchor_text` | string | *text of the URL’s anchor*<br> |
| `is_header` | boolean | *indicates if the text belongs to the header*<br> |
| `footer` | array | *content of the footer of the table*<br> |
| `row_cells` | array | *content of the row cells of the header*<br> |
| `text` | string | *text in the row cell*<br> |
| `urls` | array | *contains other URLs and anchors found in the cell*<br> |
| `url` | string | *URL found in the cell*<br> |
| `anchor_text` | string | *text of the URL’s anchor*<br> |
| `is_header` | boolean | *indicates if the text belongs to the header*<br> |
| `main_topic` | array | *main topic on the page*<br>you can find more information about topic priority calculation in this [help center article](https://dataforseo.com/help-center/difference-between-primary-and-secondary-content#topics)<br> |
| `h_title` | string | *meta title*<br> |
| `main_title` | string | * main title of the block*<br> |
| `author` | string | *content author name*<br> |
| `language` | string | *content language*<br> |
| `level` | string | *HTML level*<br> |
| `primary_content` | array | *primary content on the page*<br>you can find more information about content priority calculation in this [help center article](https://dataforseo.com/help-center/difference-between-primary-and-secondary-content)<br> |
| `text` | string | *content text*<br> |
| `url` | string | * page URL*<br>displayed in case the text is a link anchor<br> |
| `urls` | array | contains other URLs and anchors found in the content element<br> |
| `url` | string | other URL found in the content element<br> |
| `anchor_text` | string | text of the URL’s anchor<br> |
| `secondary_content` | array | *secondary content on the page*<br>you can find more information about content priority calculation in this [help center article](https://dataforseo.com/help-center/difference-between-primary-and-secondary-content)<br> |
| `text` | string | *content text*<br> |
| `url` | string | * page URL*<br>displayed in case the text is a link anchor<br> |
| `urls` | array | contains other URLs and anchors found in the content element<br> |
| `url` | string | other URL found in the content element<br> |
| `anchor_text` | string | text of the URL’s anchor<br> |
| `table_content` | array | *content of the table on the page*<br> |
| `header` | array | *content of the header of the table*<br> |
| `row_cells` | array | *content of the row cells of the header*<br> |
| `text` | string | *text in the row cell*<br> |
| `urls` | array | *contains other URLs and anchors found in the cell*<br> |
| `url` | string | *URL found in the cell*<br> |
| `anchor_text` | string | *text of the URL’s anchor*<br> |
| `is_header` | boolean | *indicates if the text belongs to the header*<br> |
| `body` | array | *content of the body of the table*<br> |
| `row_cells` | array | *content of the row cells of the header*<br> |
| `text` | string | *text in the row cell*<br> |
| `urls` | array | *contains other URLs and anchors found in the cell*<br> |
| `url` | string | *URL found in the cell*<br> |
| `anchor_text` | string | *text of the URL’s anchor*<br> |
| `is_header` | boolean | *indicates if the text belongs to the header*<br> |
| `footer` | array | *content of the footer of the table*<br> |
| `row_cells` | array | *content of the row cells of the header*<br> |
| `text` | string | *text in the row cell*<br> |
| `urls` | array | *contains other URLs and anchors found in the cell*<br> |
| `url` | string | *URL found in the cell*<br> |
| `anchor_text` | string | *text of the URL’s anchor*<br> |
| `is_header` | boolean | *indicates if the text belongs to the header*<br> |
| `secondary_topic` | array | *secondary topic on the page*<br>you can find more information about topic priority calculation in this [help center article](https://dataforseo.com/help-center/difference-between-primary-and-secondary-content#topics)<br> |
| `h_title` | string | *meta title*<br> |
| `main_title` | string | * main title of the block*<br> |
| `author` | string | *content author name*<br> |
| `language` | string | *content language*<br> |
| `level` | string | *HTML level*<br> |
| `primary_content` | array | *primary content on the page*<br>you can find more information about content priority calculation in this [help center article](https://dataforseo.com/help-center/difference-between-primary-and-secondary-content)<br> |
| `text` | string | *content text*<br> |
| `url` | string | * page URL*<br>displayed in case the text is a link anchor<br> |
| `urls` | array | contains other URLs and anchors found in the content element<br> |
| `url` | string | other URL found in the content element<br> |
| `anchor_text` | string | text of the URL’s anchor<br> |
| `secondary_content` | array | *secondary content on the page*<br>you can find more information about content priority calculation in this [help center article](https://dataforseo.com/help-center/difference-between-primary-and-secondary-content)<br> |
| `text` | string | *content text*<br> |
| `url` | string | * page URL*<br>displayed in case the text is a link anchor<br> |
| `urls` | array | contains other URLs and anchors found in the content element<br> |
| `url` | string | other URL found in the content element<br> |
| `anchor_text` | string | text of the URL’s anchor<br> |
| `table_content` | array | *content of the table on the page*<br> |
| `header` | array | *content of the header of the table*<br> |
| `row_cells` | array | *content of the row cells of the header*<br> |
| `text` | string | *text in the row cell*<br> |
| `urls` | array | *contains other URLs and anchors found in the cell*<br> |
| `url` | string | *URL found in the cell*<br> |
| `anchor_text` | string | *text of the URL’s anchor*<br> |
| `is_header` | boolean | *indicates if the text belongs to the header*<br> |
| `body` | array | *content of the body of the table*<br> |
| `row_cells` | array | *content of the row cells of the header*<br> |
| `text` | string | *text in the row cell*<br> |
| `urls` | array | *contains other URLs and anchors found in the cell*<br> |
| `url` | string | *URL found in the cell*<br> |
| `anchor_text` | string | *text of the URL’s anchor*<br> |
| `is_header` | boolean | *indicates if the text belongs to the header*<br> |
| `footer` | array | *content of the footer of the table*<br> |
| `row_cells` | array | *content of the row cells of the header*<br> |
| `text` | string | *text in the row cell*<br> |
| `urls` | array | *contains other URLs and anchors found in the cell*<br> |
| `url` | string | *URL found in the cell*<br> |
| `anchor_text` | string | *text of the URL’s anchor*<br> |
| `is_header` | boolean | *indicates if the text belongs to the header*<br> |
| `ratings` | array | *contains objects with rating information for the products displayed on the page*<br> |
| `name` | string | *rating name*<br>**Note:** this field is not used in this particular object, and its value is always set to `null` |
| `rating_value` | integer | *the value of the rating*<br> |
| `max_rating_value` | integer | *maximum value for the rating*<br> |
| `rating_count` | integer | *the amount of feedback*<br> |
| `relative_rating` | float | *relative rating*<br>can take values from `0` to `1` |
| `offers` | array | *array of products displayed on the page*<br>contains objects with information on products displayed on the page |
| `name` | string | *name of the product*<br> |
| `price` | integer | *price of the product*<br> |
| `price_currency` | string | *price currency*<br> |
| `price_valid_until` | integer | *displays the date and time until which the price is valid*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example: `"2022-11-01 10:02:52 +00:00"` |
| `comments` | array | *array of comments displayed on the page*<br>contains objects with information on comments related to displayed products |
| `rating` | object | *product’s rating*<br>contains information about the rating a customer has given to the product |
| `name` | string | *rating name*<br>**Note**: this field is not used in this particular object, and its value is always `null` |
| `rating_value` | integer | *the value of the rating*<br> |
| `max_rating_value` | integer | *maximum value for the rating*<br> |
| `rating_count` | integer | *the amount of feedback*<br>**Note**: this field is not used in this particular object, and its value is always `null` |
| `relative rating` | float | *relative rating*<br>can take values from `0` to `1` |
| `title` | string | *title of the customer’s comment*<br> |
| `publish_date` | string | *date when the comment was published*<br> |
| `author` | string | *author of the comment*<br> |
| `primary_content` | array | *primary content on the page*<br>you can find more information about content priority calculation in this [help center article](https://dataforseo.com/help-center/difference-between-primary-and-secondary-content?) |
| `text` | string | *text of the comment*<br> |
| `url` | string | *displayed in case the text is a link anchor*<br> |
| `urls` | array | *contains other URLs and anchors found in the content element*<br> |
| `contacts` | object | *contact information*<br>contains contact information displayed on the page |
| `telephones` | array | *array of telephone numbers*<br> |
| `emails` | array | *array of emails*<br> |
| `page_as_markdown` | string | *page content in the markdown format*<br>page content in the [text-to-HTML markdown format](https://daringfireball.net/projects/markdown/)<br>specify `markdown_view` as `true` in the request to return the value |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Content Parsing (Live)
*Source: [https://docs.dataforseo.com/v3/on_page/content_parsing/live/](https://docs.dataforseo.com/v3/on_page/content_parsing/live/)*
#### Live OnPage API Content Parsing

This endpoint allows parsing the content on any page you specify and will return the structured content of the target page, including link URLs, anchors, headings, and textual content.

POSThttps://api.dataforseo.com/v3/on_page/content_parsing/live

Pricing

Your account will be charged for each request.
The cost is identical to that of Instant Pages and can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page/onpage-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `url` | string | *URL of the content to parse*<br>**required field**<br>URL of the page to parse<br>example:<br>`https://www.fujielectric.com/` |
| `custom_user_agent` | string | *custom user agent*<br>optional field<br>custom user agent for crawling a website<br>example: `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36<br>`<br>default value: `Mozilla/5.0 (compatible; RSiteAuditor)` |
| `browser_preset` | string | *preset for browser screen parameters*<br>optional field<br>if you use this field, you don’t need to indicate `browser_screen_width`, `browser_screen_height`, `browser_screen_scale_factor`<br>possible values:<br>`desktop`, `mobile`, `tablet`<br>`desktop` preset will apply the following values:<br>`browser_screen_width: 1920`<br>`browser_screen_height: 1080`<br>`browser_screen_scale_factor: 1`<br>`mobile` preset will apply the following values:<br>`browser_screen_width: 390`<br>`browser_screen_height: 844`<br>`browser_screen_scale_factor: 3`<br>`tablet` preset will apply the following values:<br>`browser_screen_width: 1024`<br>`browser_screen_height: 1366`<br>`browser_screen_scale_factor: 2`<br>**Note:** to use this parameter, set `enable_javascript` or `enable_browser_rendering` to `true` |
| `browser_screen_width` | integer | *browser screen width*<br>optional field<br>you can set a custom browser screen width to perform audit for a particular device;<br>if you use this field, you don’t need to indicate `browser_preset` as it will be ignored;<br>**Note:** to use this parameter, set `enable_javascript` or `enable_browser_rendering` to `true`<br>minimum value, in pixels: `240`<br>maximum value, in pixels: `9999` |
| `browser_screen_height` | integer | *browser screen height*<br>optional field<br>you can set a custom browser screen height to perform audit for a particular device;<br>if you use this field, you don’t need to indicate `browser_preset` as it will be ignored;<br>**Note:** to use this parameter, set `enable_javascript` or `enable_browser_rendering` to `true`<br>minimum value, in pixels: `240`<br>maximum value, in pixels: `9999` |
| `browser_screen_scale_factor` | float | *browser screen scale factor*<br>optional field<br>you can set a custom browser screen resolution ratio to perform audit for a particular device;<br>if you use this field, you don’t need to indicate `browser_preset` as it will be ignored;<br>**Note:** to use this parameter, set `enable_javascript` or `enable_browser_rendering` to `true`<br>minimum value: `0.5`<br>maximum value: `3` |
| `store_raw_html` | boolean | *store HTML of a crawled page*<br>optional field<br>set to `true` if you want to get the HTML of the page using the [OnPage Raw HTML endpoint](https://docs.dataforseo.com/v3/on_page/raw_html/)<br>default value: `false` |
| `disable_cookie_popup` | boolean | *disable the cookie popup *<br>optional field<br>set to `true` if you want to disable the popup requesting cookie consent from the user;<br>default value:<br>`false`<br> |
| `accept_language` | string | *language header for accessing the website*<br>optional field<br>all locale formats are supported (xx, xx-XX, xxx-XX, etc.)<br>**Note:** if you do not specify this parameter, some websites may deny access; in this case, pages will be returned with the `"type":"broken` in the response array |
| `enable_javascript` | boolean | *load javascript on a page*<br>optional field<br>set to `true` if you want to load the scripts available on a page<br>default value: `false`<br>**Note:** if you use this parameter, additional charges will apply; learn more about the cost of tasks with this parameter [in our help article](https://dataforseo.com/help-center/cost-of-onpage-api-parameters); the cost can be calculated on the [Pricing Page](https://dataforseo.com/pricing/on-page/onpage-api) |
| `enable_browser_rendering` | boolean | *emulate browser rendering to measure Core Web Vitals*<br>optional field<br>by using this parameter you will be able to emulate a browser when loading a web page;<br>`enable_browser_rendering` loads styles, images, fonts, animations, videos, and other resources on a page;<br>default value: `false`<br>set to `true` to obtain Core Web Vitals (FID, CLS, LCP) metrics in the response;<br>**if you use this field, `enable_javascript`, and `load_resources` parameters must be set to `true`**<br>**Note:** if you use this parameter, additional charges will apply; learn more about the cost of tasks with this parameter [in our help article](https://dataforseo.com/help-center/cost-of-onpage-api-parameters); the cost can be calculated on the [Pricing Page](https://dataforseo.com/pricing/on-page/onpage-api) |
| `enable_xhr` | boolean | *enable XMLHttpRequest on a page*<br>optional field<br>set to `true` if you want our crawler to request data from a web server using the XMLHttpRequest object<br>default value:<br>`false`<br>if you use this field, `enable_javascript` must be set to `true`; |
| `switch_pool` | boolean | *switch proxy pool*<br>optional field<br>if `true`, additional proxy pools will be used to obtain the requested data;<br>the parameter can be used if a multitude of tasks is set simultaneously, resulting in occasional `rate-limit` and/or `site_unreachable` errors |
| `ip_pool_for_scan` | string | *proxy pool*<br>optional field<br>you can choose a location of the proxy pool that will be used to obtain the requested data;<br>the parameter can be used if page content is inaccessible in one of the locations, resulting in occasional `site_unreachable` errors<br>possible values: `us`, `de`<br> |
| `markdown_view` | boolean | *return page content as markdown*<br>optional field<br>if set to `true`, the markdown-formatted content of the page will be returned in the `page_as_markdown` field of the response;<br>default value: `false` |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the response array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| ** `result`** | array | *array of results* |
| `crawl_progress` | string | *status of the crawling session*<br>possible values: `in_progress`, `finished` |
| `crawl_status` | object | *details of the crawling session* |
| `items_count` | integer | *number of items in the results array*<br> |
| `items` | array | *items array*<br> |
| ***‘сontent_parsing_element’*** | | |
| `type` | string | *type of the returned item = **‘сontent_parsing_element’*** |
| `fetch_time` | string | *date and time when the content was fetched*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`"2022-11-01 10:02:52 +00:00"` |
| `status_code` | integer | *status code of the page* |
| `page_content` | object | *parsed content of the page*<br> |
| `header` | object | *parsed content of the header*<br> |
| `primary_content` | array | *primary content on the page*<br>you can find more information about content priority calculation in this [help center article](https://dataforseo.com/help-center/difference-between-primary-and-secondary-content)<br> |
| `text` | string | *content text*<br> |
| `url` | string | * page URL*<br>displayed in case the text is a link anchor<br> |
| `urls` | array | contains other URLs and anchors found in the content element<br> |
| `url` | string | other URL found in the content element<br> |
| `anchor_text` | string | text of the URL’s anchor<br> |
| `secondary_content` | array | *secondary content on the page*<br>you can find more information about content priority calculation in this [help center article](https://dataforseo.com/help-center/difference-between-primary-and-secondary-content)<br> |
| `text` | string | *content text*<br> |
| `url` | string | * page URL*<br>displayed in case the text is a link anchor<br> |
| `urls` | array | contains other URLs and anchors found in the content element<br> |
| `url` | string | other URL found in the content element<br> |
| `anchor_text` | string | text of the URL’s anchor<br> |
| `table_content` | array | *content of the table on the page*<br> |
| `header` | array | *content of the header of the table*<br> |
| `row_cells` | array | *content of the row cells of the header*<br> |
| `text` | string | *text in the row cell*<br> |
| `urls` | array | *contains other URLs and anchors found in the cell*<br> |
| `url` | string | *URL found in the cell*<br> |
| `anchor_text` | string | *text of the URL’s anchor*<br> |
| `is_header` | boolean | *indicates if the text belongs to the header*<br> |
| `body` | array | *content of the body of the table*<br> |
| `row_cells` | array | *content of the row cells of the header*<br> |
| `text` | string | *text in the row cell*<br> |
| `urls` | array | *contains other URLs and anchors found in the cell*<br> |
| `url` | string | *URL found in the cell*<br> |
| `anchor_text` | string | *text of the URL’s anchor*<br> |
| `is_header` | boolean | *indicates if the text belongs to the header*<br> |
| `footer` | array | *content of the footer of the table*<br> |
| `row_cells` | array | *content of the row cells of the header*<br> |
| `text` | string | *text in the row cell*<br> |
| `urls` | array | *contains other URLs and anchors found in the cell*<br> |
| `url` | string | *URL found in the cell*<br> |
| `anchor_text` | string | *text of the URL’s anchor*<br> |
| `is_header` | boolean | *indicates if the text belongs to the header*<br> |
| `footer` | object | *parsed content of the footer*<br> |
| `primary_content` | array | *primary content on the page*<br>you can find more information about content priority calculation in this [help center article](https://dataforseo.com/help-center/difference-between-primary-and-secondary-content)<br> |
| `text` | string | *content text*<br> |
| `url` | string | * page URL*<br>displayed in case the text is a link anchor<br> |
| `urls` | array | contains other URLs and anchors found in the content element<br> |
| `url` | string | other URL found in the content element<br> |
| `anchor_text` | string | text of the URL’s anchor<br> |
| `secondary_content` | array | *secondary content on the page*<br>you can find more information about content priority calculation in this [help center article](https://dataforseo.com/help-center/difference-between-primary-and-secondary-content)<br> |
| `text` | string | *content text*<br> |
| `url` | string | * page URL*<br>displayed in case the text is a link anchor<br> |
| `urls` | array | contains other URLs and anchors found in the content element<br> |
| `url` | string | other URL found in the content element<br> |
| `anchor_text` | string | text of the URL’s anchor<br> |
| `table_content` | array | *content of the table on the page*<br> |
| `header` | array | *content of the header of the table*<br> |
| `row_cells` | array | *content of the row cells of the header*<br> |
| `text` | string | *text in the row cell*<br> |
| `urls` | array | *contains other URLs and anchors found in the cell*<br> |
| `url` | string | *URL found in the cell*<br> |
| `anchor_text` | string | *text of the URL’s anchor*<br> |
| `is_header` | boolean | *indicates if the text belongs to the header*<br> |
| `body` | array | *content of the body of the table*<br> |
| `row_cells` | array | *content of the row cells of the header*<br> |
| `text` | string | *text in the row cell*<br> |
| `urls` | array | *contains other URLs and anchors found in the cell*<br> |
| `url` | string | *URL found in the cell*<br> |
| `anchor_text` | string | *text of the URL’s anchor*<br> |
| `is_header` | boolean | *indicates if the text belongs to the header*<br> |
| `footer` | array | *content of the footer of the table*<br> |
| `row_cells` | array | *content of the row cells of the header*<br> |
| `text` | string | *text in the row cell*<br> |
| `urls` | array | *contains other URLs and anchors found in the cell*<br> |
| `url` | string | *URL found in the cell*<br> |
| `anchor_text` | string | *text of the URL’s anchor*<br> |
| `is_header` | boolean | *indicates if the text belongs to the header*<br> |
| `main_topic` | array | *main topic on the page*<br>you can find more information about topic priority calculation in this [help center article](https://dataforseo.com/help-center/difference-between-primary-and-secondary-content#topics)<br> |
| `h_title` | string | *meta title*<br> |
| `main_title` | string | * main title of the block*<br> |
| `author` | string | *content author name*<br> |
| `language` | string | *content language*<br> |
| `level` | string | *HTML level*<br> |
| `primary_content` | array | *primary content on the page*<br>you can find more information about content priority calculation in this [help center article](https://dataforseo.com/help-center/difference-between-primary-and-secondary-content)<br> |
| `text` | string | *content text*<br> |
| `url` | string | * page URL*<br>displayed in case the text is a link anchor<br> |
| `urls` | array | contains other URLs and anchors found in the content element<br> |
| `url` | string | other URL found in the content element<br> |
| `anchor_text` | string | text of the URL’s anchor<br> |
| `secondary_content` | array | *secondary content on the page*<br>you can find more information about content priority calculation in this [help center article](https://dataforseo.com/help-center/difference-between-primary-and-secondary-content)<br> |
| `text` | string | *content text*<br> |
| `url` | string | * page URL*<br>displayed in case the text is a link anchor<br> |
| `urls` | array | contains other URLs and anchors found in the content element<br> |
| `url` | string | other URL found in the content element<br> |
| `anchor_text` | string | text of the URL’s anchor<br> |
| `table_content` | array | *content of the table on the page*<br> |
| `header` | array | *content of the header of the table*<br> |
| `row_cells` | array | *content of the row cells of the header*<br> |
| `text` | string | *text in the row cell*<br> |
| `urls` | array | *contains other URLs and anchors found in the cell*<br> |
| `url` | string | *URL found in the cell*<br> |
| `anchor_text` | string | *text of the URL’s anchor*<br> |
| `is_header` | boolean | *indicates if the text belongs to the header*<br> |
| `body` | array | *content of the body of the table*<br> |
| `row_cells` | array | *content of the row cells of the header*<br> |
| `text` | string | *text in the row cell*<br> |
| `urls` | array | *contains other URLs and anchors found in the cell*<br> |
| `url` | string | *URL found in the cell*<br> |
| `anchor_text` | string | *text of the URL’s anchor*<br> |
| `is_header` | boolean | *indicates if the text belongs to the header*<br> |
| `footer` | array | *content of the footer of the table*<br> |
| `row_cells` | array | *content of the row cells of the header*<br> |
| `text` | string | *text in the row cell*<br> |
| `urls` | array | *contains other URLs and anchors found in the cell*<br> |
| `url` | string | *URL found in the cell*<br> |
| `anchor_text` | string | *text of the URL’s anchor*<br> |
| `is_header` | boolean | *indicates if the text belongs to the header*<br> |
| `secondary_topic` | array | *secondary topic on the page*<br>you can find more information about topic priority calculation in this [help center article](https://dataforseo.com/help-center/difference-between-primary-and-secondary-content#topics)<br> |
| `h_title` | string | *meta title*<br> |
| `main_title` | string | * main title of the block*<br> |
| `author` | string | *content author name*<br> |
| `language` | string | *content language*<br> |
| `level` | string | *HTML level*<br> |
| `primary_content` | array | *primary content on the page*<br>you can find more information about content priority calculation in this [help center article](https://dataforseo.com/help-center/difference-between-primary-and-secondary-content)<br> |
| `text` | string | *content text*<br> |
| `url` | string | * page URL*<br>displayed in case the text is a link anchor<br> |
| `urls` | array | contains other URLs and anchors found in the content element<br> |
| `url` | string | other URL found in the content element<br> |
| `anchor_text` | string | text of the URL’s anchor<br> |
| `secondary_content` | array | *secondary content on the page*<br>you can find more information about content priority calculation in this [help center article](https://dataforseo.com/help-center/difference-between-primary-and-secondary-content)<br> |
| `text` | string | *content text*<br> |
| `url` | string | * page URL*<br>displayed in case the text is a link anchor<br> |
| `urls` | array | contains other URLs and anchors found in the content element<br> |
| `url` | string | other URL found in the content element<br> |
| `anchor_text` | string | text of the URL’s anchor<br> |
| `table_content` | array | *content of the table on the page*<br> |
| `header` | array | *content of the header of the table*<br> |
| `row_cells` | array | *content of the row cells of the header*<br> |
| `text` | string | *text in the row cell*<br> |
| `urls` | array | *contains other URLs and anchors found in the cell*<br> |
| `url` | string | *URL found in the cell*<br> |
| `anchor_text` | string | *text of the URL’s anchor*<br> |
| `is_header` | boolean | *indicates if the text belongs to the header*<br> |
| `body` | array | *content of the body of the table*<br> |
| `row_cells` | array | *content of the row cells of the header*<br> |
| `text` | string | *text in the row cell*<br> |
| `urls` | array | *contains other URLs and anchors found in the cell*<br> |
| `url` | string | *URL found in the cell*<br> |
| `anchor_text` | string | *text of the URL’s anchor*<br> |
| `is_header` | boolean | *indicates if the text belongs to the header*<br> |
| `footer` | array | *content of the footer of the table*<br> |
| `row_cells` | array | *content of the row cells of the header*<br> |
| `text` | string | *text in the row cell*<br> |
| `urls` | array | *contains other URLs and anchors found in the cell*<br> |
| `url` | string | *URL found in the cell*<br> |
| `anchor_text` | string | *text of the URL’s anchor*<br> |
| `is_header` | boolean | *indicates if the text belongs to the header*<br> |
| `ratings` | array | *contains objects with rating information for the products displayed on the page*<br> |
| `name` | string | *rating name*<br>**Note:** this field is not used in this particular object, and its value is always set to `null` |
| `rating_value` | integer | *the value of the rating*<br> |
| `max_rating_value` | integer | *maximum value for the rating*<br> |
| `rating_count` | integer | *the amount of feedback*<br> |
| `relative_rating` | float | *relative rating*<br>can take values from `0` to `1` |
| `offers` | array | *array of products displayed on the page*<br>contains objects with information on products displayed on the page |
| `name` | string | *name of the product*<br> |
| `price` | integer | *price of the product*<br> |
| `price_currency` | string | *price currency*<br> |
| `price_valid_until` | integer | *displays the date and time until which the price is valid*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example: `"2022-11-01 10:02:52 +00:00"` |
| `comments` | array | *array of comments displayed on the page*<br>contains objects with information on comments related to displayed products |
| `rating` | object | *product’s rating*<br>contains information about the rating a customer has given to the product |
| `name` | string | *rating name*<br>**Note**: this field is not used in this particular object, and its value is always `null` |
| `rating_value` | integer | *the value of the rating*<br> |
| `max_rating_value` | integer | *maximum value for the rating*<br> |
| `rating_count` | integer | *the amount of feedback*<br>**Note**: this field is not used in this particular object, and its value is always `null` |
| `relative rating` | float | *relative rating*<br>can take values from `0` to `1` |
| `title` | string | *title of the customer’s comment*<br> |
| `publish_date` | string | *date when the comment was published*<br> |
| `author` | string | *author of the comment*<br> |
| `primary_content` | array | *primary content on the page*<br>you can find more information about content priority calculation in this [help center article](https://dataforseo.com/help-center/difference-between-primary-and-secondary-content?) |
| `text` | string | *text of the comment*<br> |
| `url` | string | *displayed in case the text is a link anchor*<br> |
| `urls` | array | *contains other URLs and anchors found in the content element*<br> |
| `contacts` | object | *contact information*<br>contains contact information displayed on the page |
| `telephones` | array | *array of telephone numbers*<br> |
| `emails` | array | *array of emails*<br> |
| `page_as_markdown` | string | *page content in the markdown format*<br>page content in the [text-to-HTML markdown format](https://daringfireball.net/projects/markdown/)<br>specify `markdown_view` as `true` in the request to return the value |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Instant Pages (Live)
*Source: [https://docs.dataforseo.com/v3/on_page/instant_pages/](https://docs.dataforseo.com/v3/on_page/instant_pages/)*
#### OnPage API Instant Pages

Using this function you will get page-specific data with detailed information on how well a particular page is optimized for organic search.

This endpoint is working based on the Live method and doesn’t require making a separate GET request for obtaining task results.

POSThttps://api.dataforseo.com/v3/on_page/instant_pages

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page/onpage-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**You can send up to 2000 API requests per minute, with each request containing no more than 20 tasks. The maximum number of simultaneous requests you can send is limited to 30.**
**Note: in a single request, you can set up to 20 tasks each containing one URL, but these URLs cannot contain more than 5 identical domains.**

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `url` | string | *target page url*<br>**required field**<br>absolute URL of the target page;<br>**Note #1:** results will be returned for the specified URL only;<br>**Note #2:** to prevent denial-of-service events, tasks that contain a duplicate crawl host will be returned with a 40501 error;<br>to prevent this error from occurring, avoid setting tasks with the same domain if at least one of your previous tasks with this domain (including a page URL on the domain) is still in a crawling queue<br> |
| `custom_user_agent` | string | *custom user agent*<br>optional field<br>custom user agent for crawling a website<br>example: `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36<br>`<br>default value: `Mozilla/5.0 (compatible; RSiteAuditor)` |
| `browser_preset` | string | *preset for browser screen parameters*<br>optional field<br>if you use this field, you don’t need to indicate `browser_screen_width`, `browser_screen_height`, `browser_screen_scale_factor`possible values:<br>`desktop`, `mobile`, `tablet``desktop` preset will apply the following values:<br>`browser_screen_width: 1920`<br>`browser_screen_height: 1080`<br>`browser_screen_scale_factor: 1`<br>`mobile` preset will apply the following values:<br>`browser_screen_width: 390`<br>`browser_screen_height: 844`<br>`browser_screen_scale_factor: 3`<br>`tablet` preset will apply the following values:<br>`browser_screen_width: 1024`<br>`browser_screen_height: 1366`<br>`browser_screen_scale_factor: 2`<br>**Note:** to use this parameter, set `enable_javascript` or `enable_browser_rendering` to `true` |
| `browser_screen_width` | integer | *browser screen width*<br>optional field<br>you can set a custom browser screen width to perform audit for a particular device;<br>if you use this field, you don’t need to indicate `browser_preset` as it will be ignored;**Note:** to use this parameter, set `enable_javascript` or `enable_browser_rendering` to `true`minimum value, in pixels: `240`<br>maximum value, in pixels: `9999` |
| `browser_screen_height` | integer | *browser screen height*<br>optional field<br>you can set a custom browser screen height to perform audit for a particular device;<br>if you use this field, you don’t need to indicate `browser_preset` as it will be ignored;**Note:** to use this parameter, set `enable_javascript` or `enable_browser_rendering` to `true`minimum value, in pixels: `240`<br>maximum value, in pixels: `9999` |
| `browser_screen_scale_factor` | float | *browser screen scale factor*<br>optional field<br>you can set a custom browser screen resolution ratio to perform audit for a particular device;<br>if you use this field, you don’t need to indicate `browser_preset` as it will be ignored;**Note:** to use this parameter, set `enable_javascript` or `enable_browser_rendering` to `true`minimum value: `0.5`<br>maximum value: `3` |
| `store_raw_html` | boolean | *store HTML of a crawled page*<br>optional field<br>set to `true` if you want get the HTML of the page using the [OnPage Raw HTML endpoint](https://docs.dataforseo.com/v3/on_page/raw_html/)<br>default value: `false` |
| `accept_language` | string | *language header for accessing the website*<br>optional field<br>all locale formats are supported (xx, xx-XX, xxx-XX, etc.)<br>**Note:** if you do not specify this parameter, some websites may deny access; in this case, pages will be returned with the `"type":"broken` in the response array |
| `load_resources` | boolean | *load resources*<br>optional field<br>set to `true` if you want to load image, stylesheets, scripts, and broken resources<br>default value: `false`<br>**Note:** if you use this parameter, additional charges will apply; learn more about the cost of tasks with this parameter [in our help article](https://dataforseo.com/help-center/cost-of-onpage-api-parameters); the cost can be calculated on the [Pricing Page](https://dataforseo.com/pricing/on-page/onpage-api) |
| `enable_javascript` | boolean | *load javascript on a page*<br>optional field<br>set to `true` if you want to load the scripts available on a page<br>default value: `false`<br>**Note:** if you use this parameter, additional charges will apply; learn more about the cost of tasks with this parameter [in our help article](https://dataforseo.com/help-center/cost-of-onpage-api-parameters); the cost can be calculated on the [Pricing Page](https://dataforseo.com/pricing/on-page/onpage-api) |
| `enable_browser_rendering` | boolean | *emulate browser rendering to measure Core Web Vitals*<br>optional field<br>by using this parameter you will be able to emulate a browser when loading a web page;<br>`enable_browser_rendering` loads styles, images, fonts, animations, videos, and other resources on a page;<br>default value: `false`<br>set to `true` to obtain Core Web Vitals (FID, CLS, LCP) metrics in the response;<br>**if you use this field, parameters `enable_javascript`, and `load_resources` are enabled automatically;**<br>**Note:** if you use this parameter, additional charges will apply; learn more about the cost of tasks with this parameter [in our help article](https://dataforseo.com/help-center/cost-of-onpage-api-parameters); the cost can be calculated on the [Pricing Page](https://dataforseo.com/pricing/on-page/onpage-api) |
| `disable_cookie_popup` | boolean | *disable the cookie popup *<br>optional field<br>set to `true` if you want to disable the popup requesting cookie consent from the user;<br>default value:<br>`false` |
| `return_despite_timeout` | boolean | *return data on pages despite the timeout error*<br>optional field<br>if `true`, the data will be provided on pages that failed to load within 120 seconds and responded with a timeout error;<br>default value: `false` |
| `enable_xhr` | boolean | *enable XMLHttpRequest on a page*<br>optional field<br>set to `true` if you want our crawler to request data from a web server using the XMLHttpRequest object<br>default value:<br>`false`if you use this field, `enable_javascript` must be set to `true`; |
| `custom_js` | string | *custom javascript*<br>optional field`Note` that the execution time for the script you enter here should be 700 ms maximum;<br>for example, you can use the following JS snippet to check if the website contains Google Tag Manager as a `scr` attribute:<br>`let meta = { haveGoogleAnalytics: false, haveTagManager: false };\r\nfor (var i = 0; i < document.scripts.length; i++) {\r\n let src = document.scripts[i].getAttribute(\"src\");\r\n if (src != undefined) {\r\n if (src.indexOf(\"analytics.js\") >= 0)\r\n meta.haveGoogleAnalytics = true;\r\n\tif (src.indexOf(\"gtm.js\") >= 0)\r\n meta.haveTagManager = true;\r\n }\r\n}\r\nmeta;`the returned value depends on what you specified in this field. For instance, if you specify the following script:<br>`meta = {}; meta.url = document.URL; meta.test = 'test'; meta;`<br>as a response you will receive the following data:<br>`"custom_js_response": {<br>"url": "https://dataforseo.com/",<br>"test": "test"<br>}`<br> |
| `validate_micromarkup` | boolean | *enable microdata validation*<br>optional field<br>if set to `true`, you can use the [OnPage API Microdata endpoint](https://docs.dataforseo.com/v3/on_page/microdata/) with the `id` of the task;<br>default value: `false` |
| `check_spell` | boolean | *check spelling*<br>optional field<br>set to `true` to check spelling on a website using [Hunspell](http://hunspell.github.io/) library<br>default value: `false` |
| `checks_threshold` | array | *custom threshold values for checks*<br>optional field<br>you can specify custom threshold values for the parameters included in the `checks` array of OnPage API responses;<br>**Note:** only integer threshold values can be modified; |
| `switch_pool` | boolean | *switch proxy pool*<br>optional field<br>if `true`, additional proxy pools will be used to obtain the requested data;<br>the parameter can be used if a multitude of tasks is set simultaneously, resulting in occasional `rate-limit` and/or `site_unreachable` errors |
| `ip_pool_for_scan` | string | *proxy pool*<br>optional field<br>you can choose a location of the proxy pool that will be used to obtain the requested data;<br>the parameter can be used if page content is inaccessible in one of the locations, resulting in occasional `site_unreachable` errors<br>possible values: `us`, `de`<br> |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| ** `result`** | array | *array of results* |
| `crawl_progress` | string | *status of the crawling session*<br>possible values: `in_progress`, `finished` |
| `crawl_status` | object | *details of the crawling session*<br>in this case the value will be `null` |
| `crawl_gateway_address` | string | *crawler ip address*<br>displays the IP address used by the crawler to initiate the current crawling session<br>you can find the full list of IPs used by our crawler in the [Overview section](https://docs.dataforseo.com/v3/on_page/overview) |
| `total_items_count` | integer | *total number of relevant items in the database* |
| `items_count` | integer | *number of items in the results array* |
| `items` | array | *items array* |
| ***‘html’ page*** | | |
| `resource_type` | string | *type of the returned resource = **‘html’*** |
| `status_code` | integer | *status code of the page* |
| `location` | string | *location header*<br>indicates the URL to redirect a page to |
| `url` | string | *page URL* |
| `meta` | object | *page properties*<br>the value depends on the `resource_type` |
| `title` | string | *page title* |
| `charset` | integer | *[code page](https://en.wikipedia.org/wiki/Code_page)*<br>example: `65001` |
| `follow` | boolean | *indicates whether a page’s ‘meta robots’ allows crawlers to follow the links on the page*<br>if `false`, the page’s ‘meta robots’ tag contains “nofollow” parameter instructing crawlers not to follow the links on the page |
| `generator` | string | *meta tag generator* |
| `htags` | object | *HTML header tags* |
| `description` | string | *content of the meta description tag* |
| `favicon` | string | *favicon of the page* |
| `meta_keywords` | string | *content of the `keywords` meta tag* |
| `canonical` | string | *canonical page* |
| `internal_links_count` | integer | *number of internal links on the page* |
| `external_links_count` | integer | *number of external links on the page* |
| `inbound_links_count` | integer | *number of internal links pointing at the page* |
| `images_count` | integer | *number of images on the page* |
| `images_size` | integer | *total size of images on the page measured in bytes* |
| `scripts_count` | integer | *number of scripts on the page* |
| `scripts_size` | integer | *total size of scripts on the page measured in bytes* |
| `stylesheets_count` | integer | *number of stylesheets on the page* |
| `stylesheets_size` | integer | *total size of stylesheets on the page measured in bytes* |
| `title_length` | integer | *length of the `title` tag in characters* |
| `description_length` | integer | *length of the `description` tag in characters* |
| `render_blocking_scripts_count` | integer | *number of scripts on the page that block page rendering* |
| `render_blocking_stylesheets_count` | integer | *number of CSS styles on the page that block page rendering* |
| `cumulative_layout_shift` | float | *Core Web Vitals metric measuring the layout stability of the page*<br>measures the sum total of all individual layout shift scores for every unexpected layout shift that occurs during the entire lifespan of the page. [Learn more.](https://web.dev/cls/) |
| `meta_title` | string | *meta title of the page*<br>meta tag in the head section of an HTML document that defines the title of a page |
| `content` | object | *overall information about content of the page* |
| `plain_text_size` | integer | *total size of the text on the page measured in bytes* |
| `plain_text_rate` | integer | *plaintext rate value*<br>`plain_text_size` to `size` ratio |
| `plain_text_word_count` | float | *number of words on the page* |
| `automated_readability_index` | float | *[Automated Readability Index](https://en.wikipedia.org/wiki/Automated_readability_index)* |
| `coleman_liau_readability_index` | float | *[Coleman–Liau Index](https://en.wikipedia.org/wiki/Coleman%E2%80%93Liau_index)* |
| `dale_chall_readability_index` | float | *[Dale–Chall Readability Index](https://en.wikipedia.org/wiki/Dale%E2%80%93Chall_readability_formula)* |
| `flesch_kincaid_readability_index` | float | *[Flesch–Kincaid Readability Index](https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests)* |
| `smog_readability_index` | float | *[SMOG Readability Index](https://en.wikipedia.org/wiki/SMOG)* |
| `description_to_content_consistency` | float | *consistency of the meta `description` tag with the page content*<br>measured from 0 to 1 |
| `title_to_content_consistency` | float | *consistency of the meta `title` tag with the page content*<br>measured from 0 to 1 |
| `meta_keywords_to_content_consistency` | float | *consistency of meta `keywords`tag with the page content*<br>measured from 0 to 1 |
| `deprecated_tags` | array | *deprecated tags on the page* |
| `duplicate_meta_tags` | array | *duplicate meta tags on the page* |
| `spell` | object | *spellcheck*<br>[hunspell](http://hunspell.github.io/) spellcheck errors |
| `hunspell_language_code` | string | *spellcheck language code* |
| `misspelled` | array | *array of misspelled words* |
| `word` | string | *misspelled word* |
| `social_media_tags` | object | *object of social media tags found on the page*<br>contains social media tags and their content<br>supported tags include but are not limited to [Open Graph](https://ogp.me/) and [Twitter card](https://developer.twitter.com/en/docs/twitter-for-websites/cards/guides/getting-started) |
| `page_timing` | object | *object of page load metrics* |
| `time_to_interactive` | integer | *[Time To Interactive (TTI)](https://web.dev/interactive/) metric*<br>the time it takes until the user can interact with a page (in milliseconds) |
| `dom_complete` | integer | *time to load resources*<br>the time it takes until the page and all of its subresources are downloaded (in milliseconds) |
| `largest_contentful_paint` | float | *Core Web Vitals metric measuring how fast the largest above-the-fold content element is displayed*<br>The amount of time (in milliseconds) to render the largest content element visible in the viewport, from when the user requests the URL. [Learn more](https://web.dev/lcp/). |
| `first_input_delay` | float | *Core Web Vitals metric indicating the responsiveness of a page*<br>The time (in milliseconds) from when a user first interacts with your page to the time when the browser responds to that interaction. [Learn more](https://web.dev/fid/). |
| `connection_time` | integer | *time to connect to a server*<br>the time it takes until the connection with a server is established (in milliseconds) |
| `time_to_secure_connection` | integer | *time to establish a secure connection*<br>the time it takes until the secure connection with a server is established (in milliseconds) |
| `request_sent_time` | integer | *time to send a request to a server*<br>the time it takes until the request to a server is sent (in milliseconds) |
| `waiting_time` | integer | *time to first byte [(TTFB)](https://en.wikipedia.org/wiki/Time_to_first_byte) in milliseconds* |
| `download_time` | integer | *time it takes for a browser to receive a response (in milliseconds)* |
| `duration_time` | integer | *total time it takes until a browser receives a complete response from a server (in milliseconds)* |
| `fetch_start` | integer | *time to start downloading the HTML resource*<br>the amount of time the browser needs to start downloading a page |
| `fetch_end` | integer | *time to complete downloading the HTML resource*<br>the amount of time the browser needs to complete downloading a page |
| `onpage_score` | float | *shows how page is optimized on a 100-point scale*<br>this field shows how page is optimized considering critical on-page issues and warnings detected;<br>`100` is the highest possible score that means the page does not have any critical on-page issues and important warnings;<br>learn more about how the metric is calculated in [this help center article](https://dataforseo.com/help-center/how-on-page-seo-score-is-calculated) |
| `total_dom_size` | integer | *total [DOM](https://developers.google.com/web/tools/chrome-devtools/dom) size of a page* |
| `custom_js_response` | string/object/integer | *the result of executing a specified JS script*<br>**note** that you should specify a `custom_js` field when [setting a task](https://docs.dataforseo.com/v3/on_page/task_post/) to receive this data and the field type and its value will totally depend on the script you specified;<br>you can also filter the results by this value specifying `filters` in the following way:<br>`["custom_js_response.url", "like", "pixel"]` |
| `custom_js_client_exception` | string | *error when executing a custom js*<br>if the error occurred when executing the script you specified in the `custom_js` field, the error message would be displayed here |
| `resource_errors` | object | *resource errors and warnings* |
| `errors` | array | *resource errors* |
| `line` | integer | *line where the error was found* |
| `column` | integer | *column where the error was found* |
| `message` | string | *text message of the error*<br>the full list of possible HTML errors can be found [here](https://github.com/AngleSharp/AngleSharp/blob/3968eb050e142b1d94550fba407afe772232b126/src/AngleSharp/Html/Parser/HtmlParseError.cs) |
| `status_code` | integer | *status code of the error*<br>possible values:<br>`0` — Unidentified Error;<br>`501` — Html Parse Error;<br>`1501` — JS Parse Error;<br>`2501` — CSS Parse Error;<br>`3501` — Image Parse Error;<br>`3502` — Image Scale Is Zero;<br>`3503` — Image Size Is Zero;<br>`3504` — Image Format Invalid |
| `warnings` | array | *resource warnings* |
| `line` | integer | *line the warning relates to*<br>note that if `"line": 0`, the warning relates to the whole page |
| `column` | integer | *column the warning relates to*<br>note that if `"column": 0`, the warning relates to the whole page |
| `message` | string | *text message of the warning*<br>possible messages:<br>`"Has node with more than 60 childs."` – HTML page has at least 1 tag nesting over 60 tags of the same level<br>`"Has more that 1500 nodes."` – DOM tree contains over 1,500 elements<br>`"HTML depth more than 32 tags."` – DOM depth exceeds 32 nodes |
| `status_code` | integer | *status code of the warning*<br>possible values:<br>`0` — Unidentified Warning;<br>`1` — Has node with more than 60 childs;<br>`2` — Has more that 1500 nodes;<br>`3` — HTML depth more than 32 tags |
| `broken_resources` | boolean | *indicates whether a page contains broken resources* |
| `broken_links` | boolean | *indicates whether a page contains broken links* |
| `duplicate_title` | boolean | *indicates whether a page has duplicate `title` tags* |
| `duplicate_description` | boolean | *indicates whether a page has a duplicate description* |
| `duplicate_content` | boolean | *indicates whether a page has duplicate content* |
| `click_depth` | integer | *number of clicks it takes to get to the page*<br>indicates the number of clicks from the homepage needed before landing at the target page |
| `size` | integer | *resource size*<br>indicates the size of a given page measured in bytes |
| `encoded_size` | integer | *page size after encoding*<br>indicates the size of the encoded page measured in bytes |
| `total_transfer_size` | integer | *compressed page size*<br>indicates the compressed size of a given page |
| `fetch_time` | string | *date and time when a resource was fetched*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `cache_control` | object | *instructions for caching* |
| `cachable` | boolean | *indicates whether the page is cacheable* |
| `ttl` | integer | *time to live*<br>the amount of time the browser caches a resource |
| `checks` | object | *website checks*<br>on-page check-ups related to the page |
| `no_content_encoding` | boolean | *page with no content encoding*<br>indicates whether a page has no [compression algorithm](http://www.iana.org/assignments/http-parameters/http-parameters.xhtml#content-coding) of the content |
| `high_loading_time` | boolean | *page with high loading time*<br>indicates whether a page loading time exceeds 3 seconds |
| `is_redirect` | boolean | *page with redirects*<br>indicates whether a page has `3XX` redirects to other pages |
| `is_4xx_code` | boolean | *page with `4xx` status codes*<br>indicates whether a page has `4xx` response code |
| `is_5xx_code` | boolean | *page with `5xx` status codes*<br>indicates whether a page has `5xx` response code |
| `is_broken` | boolean | *broken page*<br>indicates whether a page returns a response code less than `200` or greater than `400` |
| `is_www` | boolean | *page with www*<br>indicates whether a page is on a `www` subdomain |
| `is_https` | boolean | *page with the https protocol* |
| `is_http` | boolean | *page with the http protocol* |
| `high_waiting_time` | boolean | *page with high waiting time*<br>indicates whether a page waiting time (aka Time to First Byte) exceeds 1.5 seconds |
| `has_micromarkup` | boolean | *page contains [microdata markup](https://en.wikipedia.org/wiki/Microdata_(HTML))*<br>indicates whether a page is without the `<!DOCTYPE HTML>` declaration |
| `has_micromarkup_errors` | boolean | *page contains microdata markup errors*<br>indicates whether a page is without the `<!DOCTYPE HTML>` declaration |
| `no_doctype` | boolean | *page with no doctype*<br>indicates whether a page is without the `<!DOCTYPE HTML>` declaration |
| `has_html_doctype` | boolean | *page with HTML doctype declaration*<br>if `true`, the page has HTML `DOCTYPE` declaration |
| `canonical` | boolean | *page is canonical* |
| `no_encoding_meta_tag` | boolean | *page with no meta tag encoding*<br>indicates whether a page is without `Content-Type`;<br>informative only if the encoding is not explicit in the `Content-Type` header;<br>example: `Content-Type: "text/html; charset=utf8"`<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_h1_tag` | boolean | *page with empty or absent h1 tags*<br>**Note:** available for pages with `canonical` check set to `true` |
| `https_to_http_links` | boolean | *HTTPS page has links to HTTP pages*<br>if `true`, this `HTTPS` page has links to `HTTP` pages;<br>**Note:** available for pages with `canonical` check set to `true` |
| `size_greater_than_3mb` | boolean | *page with size larger than 3 MB*<br>if `true`, the page size is exceeding 3 MB<br>**Note:** available for pages with `canonical` check set to `true` |
| `meta_charset_consistency` | boolean | *consistency between charset encoding and page charset*<br>if `true`, the page’s charset encoding doesn’t match the actual charset of the page;<br>**Note:** available for pages with `canonical` check set to `true` |
| `has_meta_refresh_redirect` | boolean | *pages with meta refresh redirect*<br>if `true`, the page has <meta http-equiv=”refresh”> tag that instructs a browser to load another page after a specified time span;<br>**Note:** available for pages with `canonical` check set to `true` |
| `has_render_blocking_resources` | boolean | *page with render-blocking resources*<br>if `true`, the page has render-blocking scripts or stylesheets;<br>**Note:** available for pages with `canonical` check set to `true` |
| `low_content_rate` | boolean | *page with low content rate*<br>indicates whether a page has the `plaintext size` to `page size` ratio of less than 0.1;<br>**Note:** available for pages with `canonical` check set to `true` |
| `high_content_rate` | boolean | *page with high content rate*<br>indicates whether a page has the `plaintext size` to `page size` ratio of more than 0.9<br>**Note:** available for pages with `canonical` check set to `true` |
| `low_character_count` | boolean | *indicates whether the page has less than 1024 characters*<br>**Note:** available for pages with `canonical` check set to `true` |
| `high_character_count` | boolean | *indicates whether the page has more than 256,000 characters*<br>**Note:** available for pages with `canonical` check set to `true` |
| `small_page_size` | boolean | *indicates whether a page is too small*<br>the value will be `true` if a page size is smaller than 1024 bytes;<br>**Note:** available for pages with `canonical` check set to `true` |
| `large_page_size` | boolean | *indicates whether a page is too heavy*<br>the value will be `true` if a page size exceeds 1 megabyte;<br>**Note:** available for pages with `canonical` check set to `true` |
| `low_readability_rate` | boolean | *page with a low readability rate*<br>indicates whether a page is scored less than 15 points on the [Flesch–Kincaid readability test](https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests);<br>**Note:** available for pages with `canonical` check set to `true` |
| `irrelevant_description` | boolean | *page with irrelevant description*<br>indicates whether a page `description` tag is irrelevant to the content of a page;<br>the relevance threshold is `0.2`;<br>**Note:** available for pages with `canonical` check set to `true` |
| `irrelevant_title` | boolean | *page with irrelevant title*<br>indicates whether a page `title` tag is irrelevant to the content of the page;<br>the relevance threshold is `0.3`;<br>**Note:** available for pages with `canonical` check set to `true` |
| `irrelevant_meta_keywords` | boolean | *page with irrelevant meta keywords*<br>indicates whether a page `keywords` tags are irrelevant to the content of a page;<br>the relevance threshold is `0.6`;<br>**Note:** available for pages with `canonical` check set to `true` |
| `title_too_long` | boolean | *page with a long title*<br>indicates whether the content of the `title` tag exceeds 65 characters;<br>**Note:** available for pages with `canonical` check set to `true` |
| `has_meta_title` | boolean | *page has a meta title*<br>indicates whether the HTML of a page contains the `meta_title` tag;<br>**Note:** available for pages with `canonical` check set to `true` |
| `title_too_short` | boolean | *page with short titles*<br>indicates whether the content of `title` tag is shorter than 30 characters;<br>**Note:** available for pages with `canonical` check set to `true` |
| `deprecated_html_tags` | boolean | *page with deprecated tags*<br>indicates whether a page has [deprecated HTML tags](https://www.codehelp.co.uk/html/deprecated.html);<br>**Note:** available for pages with `canonical` check set to `true` |
| `duplicate_meta_tags` | boolean | *page with duplicate meta tags*<br>indicates whether a page has more than one meta tag of the same type;<br>**Note:** available for pages with `canonical` check set to `true` |
| `duplicate_title_tag` | boolean | *page with more than one title tag*<br>indicates whether a page has more than one `title` tag;<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_image_alt` | boolean | *images without `alt` tags*<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_image_title` | boolean | *images without `title` tags*<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_description` | boolean | *pages with no description*<br>indicates whether a page has an empty or absent `description` meta tag;<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_title` | boolean | *page with no title*<br>indicates whether a page has an empty or absent `title` tag;<br>**Note:** available for pages with `canonical` check set to `true` |
| `no_favicon` | boolean | *page with no favicon*<br>**Note:** available for pages with `canonical` check set to `true` |
| `seo_friendly_url` | boolean | *page with seo-frienldy URL*<br>the ‘SEO-friendliness’ of a page URL is checked by four parameters:<br>– the length of the relative path is less than 120 characters<br>– no special characters<br>– no dynamic parameters<br>– relevance of the URL to the page<br>if at least one of them is failed then such URL is considered as not ‘SEO-friendly’<br>**Note:** available for pages with `canonical` check set to `true` |
| `flash` | boolean | *page with flash*<br>indicates whether a page has flash elements |
| `frame` | boolean | *page with frames*<br>indicates whether a page contains `frame`, `iframe`, `frameset` tags |
| `lorem_ipsum` | boolean | *page with lorem ipsum*<br>indicates whether a page has *lorem ipsum* content;<br>**Note:** available for pages with `canonical` check set to `true` |
| `has_misspelling` | boolean | *page with misspelling*<br>indicates whether a page has *spelling* mistakes<br>informative if the `check_spell` was set to `true` in the POST array |
| `seo_friendly_url_characters_check` | boolean | *URL characters check-up*<br>indicates whether a page URL containing only uppercase and lowercase Latin characters, digits and dashes |
| `seo_friendly_url_dynamic_check` | boolean | *URL dynamic check-up*<br>the value will be `true` if a page has no dynamic parameters in the url |
| `seo_friendly_url_keywords_check` | boolean | *URL keyword check-up*<br>indicates whether a page URL is consistent with the `title` meta tag |
| `seo_friendly_url_relative_length_check` | boolean | *URL length check-up*<br>the value will be `true` if a page URL no longer than 120 characters |
| `content_encoding` | string | *type of encoding* |
| `media_type` | string | *types of media used to display a page* |
| `server` | string | *server version* |
| `is_resource` | boolean | *indicates whether a page is a single resource* |
| `url_length` | integer | *page URL length in characters* |
| `relative_url_length` | integer | *relative URL length in characters* |
| `last_modified` | object | *contains data on changes related to the resource*<br>if there is no data, the value will be `null` |
| `header` | string | *date and time when the header was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| `sitemap` | string | *date and time when the sitemap was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| `meta_tag` | string | *date and time when the meta tag was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| ***‘broken’ page*** | | |
| `resource_type` | string | *type of the returned resource = **‘broken’*** |
| `status_code` | integer | *status code of the page* |
| `location` | string | *location header*<br>indicates the URL to redirect a page to |
| `url` | string | *page URL* |
| `size` | integer | *resource size*<br>indicates the size of a given page measured in bytes |
| `encoded_size` | integer | *page size after encoding*<br>indicates the size of the encoded page measured in bytes |
| `total_transfer_size` | integer | *compressed page size*<br>indicates the compressed size of a given page |
| `fetch_time` | string | *date and time when a resource was fetched*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `fetch_timing` | object | *time range within which a result was fetched* |
| `duration_time` | integer | *indicates how many seconds it took to download a page* |
| `fetch_start` | integer | *time to start downloading the HTML resource*<br>the amount of time the browser needs to start downloading a page |
| `fetch_end` | integer | *time to complete downloading the HTML resource*<br>the amount of time the browser needs to complete downloading a page |
| `cache_control` | object | *instructions for caching* |
| `cachable` | boolean | *indicates whether the page is cacheable* |
| `ttl` | integer | *time to live*<br>the amount of time the browser caches a resource |
| `checks` | object | *on-page check-ups* |
| `no_content_encoding` | boolean | *page with no content encoding*<br>indicates whether a page has no [compression algorithm](http://www.iana.org/assignments/http-parameters/http-parameters.xhtml#content-coding) of the content |
| `high_loading_time` | boolean | *page with high loading time*<br>indicates whether a page loading time exceeds 3 seconds |
| `is_redirect` | boolean | *page with redirects*<br>indicates whether a page has `3XX` redirects to other pages |
| `is_4xx_code` | boolean | *page with with `4xx` status code*<br>indicates whether a page has `4XX` response code |
| `is_5xx_code` | boolean | *page with `5xx` status code*<br>indicates whether a page has `5XX` response code |
| `is_broken` | boolean | *broken page*<br>indicates whether a page returns a response code less than `200` or greater than `400` |
| `is_www` | boolean | *page with www*<br>indicates whether a page is on a `www` subdomain |
| `is_https` | boolean | *page with the https protocol* |
| `is_http` | boolean | *page with the http protocol* |
| `resource_errors` | object | *resource errors and warnings* |
| `errors` | array | *resource errors* |
| `line` | integer | *line where the error was found* |
| `column` | integer | *column where the error was found* |
| `message` | string | *text message of the error*<br>the full list of possible HTML errors can be found [here](https://github.com/AngleSharp/AngleSharp/blob/3968eb050e142b1d94550fba407afe772232b126/src/AngleSharp/Html/Parser/HtmlParseError.cs) |
| `status_code` | integer | *status code of the error*<br>possible values:<br>`0` — Unidentified Error;<br>`501` — Html Parse Error;<br>`1501` — JS Parse Error;<br>`2501` — CSS Parse Error;<br>`3501` — Image Parse Error;<br>`3502` — Image Scale Is Zero;<br>`3503` — Image Size Is Zero;<br>`3504` — Image Format Invalid |
| `warnings` | array | *resource warnings* |
| `line` | integer | *line the warning relates to*<br>note that if `"line": 0`, the warning relates to the whole page |
| `column` | integer | *columnthe warning relates to*<br>note that if `"column": 0`, the warning relates to the whole page |
| `message` | string | *text message of the warning*<br>possible messages:<br>`"Has node with more than 60 childs."` – HTML page has at least 1 tag nesting over 60 tags of the same level<br>`"Has more that 1500 nodes."` – DOM tree contains over 1,500 elements<br>`"HTML depth more than 32 tags."` – DOM depth exceeds 32 nodes |
| `status_code` | integer | *status code of the warning*<br>possible values:<br>`0` — Unidentified Warning;<br>`1` — Has node with more than 60 childs;<br>`2` — Has more that 1500 nodes;<br>`3` — HTML depth more than 32 tags |
| `content_encoding` | string | *type of encoding* |
| `media_type` | string | *types of media used to display a page*<br>example: `"text/html"` |
| `server` | string | *server version* |
| `is_resource` | boolean | *indicates whether a page is a single resource* |
| `last_modified` | object | *contains data on changes related to the resource*<br>if there is no data, the value will be `null` |
| `header` | string | *date and time when the header was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| `sitemap` | string | *date and time when the sitemap was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| `meta_tag` | string | *date and time when the meta tag was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| ***‘redirect’ page*** | | |
| `resource_type` | string | *type of the returned resource = **‘redirect’*** |
| `status_code` | integer | *status code of the page* |
| `location` | string | *location header*<br>**target URL** for “redirect” resources |
| `url` | string | *page url*<br>**source URL** for “redirect” resources |
| `size` | integer | *resource size*<br>indicates the size of a given page measured in bytes<br>equals `0` for “redirect” resources |
| `encoded_size` | integer | *page size after encoding*<br>equals `0` for “redirect” resources |
| `total_transfer_size` | integer | *compressed page size*<br>indicates the compressed size of a given page |
| `fetch_time` | string | *date and time when a resource was fetched*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `fetch_timing` | object | *time range within which a result was fetched* |
| `duration_time` | integer | *indicates how many seconds it took to download a page* |
| `fetch_start` | integer | *time to start downloading the HTML resource*<br>the amount of time the browser needs to start downloading a page |
| `fetch_end` | integer | *time to complete downloading the HTML resource*<br>the amount of time the browser needs to complete downloading a page |
| `resource_errors` | object | *resource errors and warnings* |
| `errors` | array | *resource errors* |
| `line` | integer | *line where the error was found* |
| `column` | integer | *column where the error was found* |
| `message` | string | *text message of the error*<br>the full list of possible HTML errors can be found [here](https://github.com/AngleSharp/AngleSharp/blob/3968eb050e142b1d94550fba407afe772232b126/src/AngleSharp/Html/Parser/HtmlParseError.cs) |
| `status_code` | integer | *status code of the error*<br>possible values:<br>`0` — Unidentified Error;<br>`501` — Html Parse Error;<br>`1501` — JS Parse Error;<br>`2501` — CSS Parse Error;<br>`3501` — Image Parse Error;<br>`3502` — Image Scale Is Zero;<br>`3503` — Image Size Is Zero;<br>`3504` — Image Format Invalid |
| `warnings` | array | *resource warnings* |
| `line` | integer | *line the warning relates to*<br>note that if `"line": 0`, the warning relates to the whole page |
| `column` | integer | *column the warning relates to*<br>note that if `"column": 0`, the warning relates to the whole page |
| `message` | string | *text message of the warning*<br>possible messages:<br>`"Has node with more than 60 childs."` – HTML page has at least 1 tag nesting over 60 tags of the same level<br>`"Has more that 1500 nodes."` – DOM tree contains over 1,500 elements<br>`"HTML depth more than 32 tags."` – DOM depth exceeds 32 nodes |
| `status_code` | integer | *status code of the warning*<br>possible values:<br>`0` — Unidentified Warning;<br>`1` — Has node with more than 60 childs;<br>`2` — Has more that 1500 nodes;<br>`3` — HTML depth more than 32 tags |
| `cache_control` | object | *instructions for caching* |
| `cachable` | boolean | *indicates whether the page is cacheable* |
| `ttl` | integer | *time to live*<br>the amount of time the browser caches a resource |
| `checks` | object | *on-page check-ups* |
| `no_content_encoding` | boolean | *page with no content encoding*<br>indicates whether a page has no [compression algorithm](http://www.iana.org/assignments/http-parameters/http-parameters.xhtml#content-coding) of the content |
| `high_loading_time` | boolean | *page with high loading time*<br>indicates whether a page loading time exceeds 3 seconds |
| `is_redirect` | boolean | *page with redirects*<br>indicates whether a page has `3XX` redirects to other pages |
| `is_4xx_code` | boolean | *page with `4xx` status codes*<br>indicates whether a page has `4xx` response code |
| `is_5xx_code` | boolean | *page with `5xx` status codes*<br>indicates whether a page has `5xx` response code |
| `is_broken` | boolean | *broken page*<br>indicates whether a page returns a response code less than `200` or greater than `400` |
| `is_www` | boolean | *page with www*<br>indicates whether a page is on a `www` subdomain |
| `is_https` | boolean | *page with the https protocol* |
| `is_http` | boolean | *page with the http protocol* |
| `content_encoding` | string | *type of encoding* |
| `media_type` | string | *types of media used to display a page*<br>example: `"text/html"` |
| `server` | string | *server version* |
| `is_resource` | boolean | *indicates whether a page is a single resource* |
| `last_modified` | object | *contains data on changes related to the resource*<br>if there is no data, the value will be `null` |
| `header` | string | *date and time when the header was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| `sitemap` | string | *date and time when the sitemap was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| `meta_tag` | string | *date and time when the meta tag was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| ***resources*** | | *Note: the following types of resources will be displayed only if the first URL to crawl is a script, image, or stylesheet* |
| `resource_type` | string | *type of the returned resource*<br>possible types: `script`, `image`, `stylesheet` |
| `meta` | object | *resource properties*<br>available only for items with the following `resource_type`: `image` |
| `alternative_text` | string | *content of the image `alt` attribute* |
| `title` | string | *title* |
| `original_width` | integer | *original image width in px* |
| `original_height` | integer | *original image height in px* |
| `width` | integer | *image width in px* |
| `height` | integer | *image height in px* |
| `status_code` | integer | *status code of the page where a given resource is located* |
| `location` | string | *location header*<br>indicates the URL to redirect a page to |
| `url` | string | *resource URL* |
| `size` | integer | *resource size*<br>indicates the size of a given resource measured in bytes |
| `encoded_size` | integer | *resource size after encoding*<br>indicates the size of the encoded resource measured in bytes |
| `total_transfer_size` | integer | *compressed resource size*<br>indicates the compressed size of a given resource in bytes |
| `fetch_time` | string | *date and time when a resource was fetched*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2021-02-17 13:54:15 +00:00` |
| `fetch_timing` | object | *resource fetching time range* |
| `duration_time` | integer | *indicates how many milliseconds it took to fetch a resource* |
| `fetch_start` | integer | *time to start downloading the resource*<br>the amount of time a browser needs to start downloading a resource |
| `fetch_end` | integer | *time to complete downloading the resource*<br>the amount of time a browser needs to complete downloading a resource |
| `cache_control` | object | *instructions for caching* |
| `cachable` | boolean | *indicates whether the resource is cacheable* |
| `ttl` | integer | *time to live*<br>the amount of time it takes for the browser to cache a resource; measured in milliseconds |
| `checks` | object | *resource check-ups*<br>contents of the array depend on the `resource_type` |
| `no_content_encoding` | boolean | *resource with no content encoding*<br>indicates whether a page has no [compression algorithm](http://www.iana.org/assignments/http-parameters/http-parameters.xhtml#content-coding) of the content; |
| `high_loading_time` | boolean | *resource with high loading time*<br>indicates whether a resource loading time exceeds 3 seconds; |
| `is_redirect` | boolean | *resource with redirects*<br>indicates whether a page with a resource has `3XX` redirects to other pages; |
| `is_4xx_code` | boolean | *resource with `4xx` status codes*<br>indicates whether a resource has `4xx` response code |
| `is_5xx_code` | boolean | *resource with `5xx` status codes*<br>indicates whether a resource has `5xx` response code |
| `is_broken` | boolean | *broken resource*<br>indicates whether a page with this resource returns `4xx`, `5xx` response codes or has broken elements inside the resource |
| `is_www` | boolean | *page with www*<br>indicates whether a page with this resource is on a `www` subdomain |
| `is_https` | boolean | *page with the https protocol* |
| `is_http` | boolean | *page with the http protocol* |
| `is_minified` | boolean | *resource is minified*<br>indicates whether the content of a stylesheet or script is minified;<br>available for items with the following `resource_type`: `stylesheet`, `script` |
| `has_redirect` | boolean | *resource has a redirect*<br>available for items with the following `resource_type`: `script`, `image`;<br>if the `resource_type` is `image`, this field will indicate whether other pages and/or resources have redirects pointing at the image;<br>if the `resource_type` is `script`, this field will indicate whether the script contains a redirect |
| `has_subrequests` | boolean | *resource contains subrequests*<br>indicates whether the content of a stylesheet or script contain additional requests;<br>available for items with the following `resource_type`: `stylesheet`, `script` |
| `original_size_displayed` | boolean | *image desplayes in its original size*<br>indicates whether the image is displayed in its original size;<br>available only for items with the following `resource_type`: `image` |
| `resource_errors` | object | *resource errors and warnings* |
| `errors` | array | *resource errors* |
| `line` | integer | *line where the error was found* |
| `column` | integer | *column where the error was found* |
| `message` | string | *text message of the error*<br>the full list of possible HTML errors can be found [here](https://github.com/AngleSharp/AngleSharp/blob/3968eb050e142b1d94550fba407afe772232b126/src/AngleSharp/Html/Parser/HtmlParseError.cs) |
| `status_code` | integer | *status code of the error*<br>possible values:<br>`0` — Unidentified Error;<br>`501` — Html Parse Error;<br>`1501` — JS Parse Error;<br>`2501` — CSS Parse Error;<br>`3501` — Image Parse Error;<br>`3502` — Image Scale Is Zero;<br>`3503` — Image Size Is Zero;<br>`3504` — Image Format Invalid |
| `warnings` | array | *resource warnings* |
| `line` | integer | *line the warning relates to*<br>note that if `"line": 0`, the warning relates to the whole page |
| `column` | integer | *column the warning relates to*<br>note that if `"column": 0`, the warning relates to the whole page |
| `message` | string | *text message of the warning*<br>possible messages:<br>`"Has node with more than 60 childs."` – HTML page has at least 1 tag nesting over 60 tags of the same level<br>`"Has more that 1500 nodes."` – DOM tree contains over 1,500 elements<br>`"HTML depth more than 32 tags."` – DOM depth exceeds 32 nodes |
| `status_code` | integer | *status code of the warning*<br>possible values:<br>`0` — Unidentified Warning;<br>`1` — Has node with more than 60 childs;<br>`2` — Has more that 1500 nodes;<br>`3` — HTML depth more than 32 tags |
| `content_encoding` | string | *type of encoding* |
| `media_type` | string | *types of media used to display a resource* |
| `accept_type` | string | *indicates the expected type of resource*<br>for example, if `"resource_type": "broken"`, `accept_type` will indicate the type of the broken resource<br>possible values:<br>`any`, `none`, `image`, `sitemap`, `robots`, `script`, `stylesheet`, `redirect`, `html`, `text`, `other`, `font` |
| `server` | string | *server version* |
| `last_modified` | object | *contains data on changes related to the resource*<br>if there is no data, the value will be `null` |
| `header` | string | *date and time when the header was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| `sitemap` | string | *date and time when the sitemap was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |
| `meta_tag` | string | *date and time when the meta tag was last modified*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br>if there is no data, the value will be `null` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Overview
*Source: [https://docs.dataforseo.com/v3/on_page/lighthouse/overview/](https://docs.dataforseo.com/v3/on_page/lighthouse/overview/)*
### OnPage Lighthouse API: Overview

The OnPage Lighthouse API is based on Google's open-source Lighthouse project and provides data on the quality of web pages.

The OnPage Lighthouse API is a tool for leveraging the capabilities of Lighthouse – Google’s open-source project intended to help webmasters access the data on the performance and quality of web pages and web apps.

Lighthouse reports the performance metrics simulating a mid-tier mobile device on a 4G internet connection. To achieve that, Lighthouse incorporates sophisticated architecture, illustrated below. You can get more information about how Lighthouse works by visiting the official documentation of Google’s Lighthouse project.

*Note that OnPage Lighthouse API is based on Google’s open-source [Lighthouse project](https://github.com/GoogleChrome/lighthouse/). The data returned in the `results` array of the API’s response is identical to that described in the project’s [official documentation](https://github.com/GoogleChrome/lighthouse/tree/master/docs). You can refer to it for more information about the content and structure of the data provided by OnPage Lighthouse API. *

Sending a web page for crawling is done through a POST request to the [Lighthouse Task POST](https://docs.dataforseo.com/v3/on_page/lighthouse/task_post/) endpoint. Alongside the URL of the web page, you can specify additional parameters, which would help you filter the data and get the results you need:

**● Audits** contain the results of the audits and keyed by their titles; to get only certain audits, you should specify their titles in the corresponding Task POST array; you can obtain the list of titles of all available audits by requesting the [Lighthouse Audits endpoint](https://docs.dataforseo.com/v3/on_page/lighthouse/audits/).
**● Categories** contain different categories, their scores, and references to the audits that comprise them.

After the website is fetched for crawling, you can start retrieving results by passing the `task_id` of the tasks in the [Lighthouse Task GET](https://docs.dataforseo.com/v3/on_page/lighthouse/task_get/json) endpoint. For now, you can obtain results in JSON only, but we plan to add support for HTML in the nearest future.

Learn more about task completion and obtaining a list of completed tasks in [this help center article.](https://dataforseo.com/help-center/completed-tasks)

Alternatively, you can specify `pingback_url` or `postback_url` when setting a task, and we will notify you on completion of tasks or send the results to you respectively.

If you do use `pingback_url` or `postback_url`, you can receive the list of id for all completed tasks using the [Tasks Ready](https://docs.dataforseo.com/v3/on_page/lighthouse/tasks_ready/) endpoint. It is designed to provide you with a list of completed tasks, which haven’t been collected yet.

You can send up to 2000 API calls per minute, with each POST call containing no more than 100 tasks. Contact us if you would like to raise the limit. Note that the maximum number of simultaneous requests you can send is limited to 30.

If your system requires delivering instant results, the [Lighthouse Live](https://docs.dataforseo.com/v3/on_page/lighthouse/live/json) endpoint is the best solution for you as it doesn’t require making separate POST and GET requests to the corresponding endpoints.

You can test the Lighthouse OnPage API for free using DataForSEO [Sandbox.](https://docs.dataforseo.com/v3/appendix/sandbox/)

**The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page/lighthouse-api) page or by making a separate call to [the User Data endpoint.](https://docs.dataforseo.com/v3/appendix/user_data/?php)**

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

---


#### Languages
*Source: [https://docs.dataforseo.com/v3/on_page/lighthouse/languages/](https://docs.dataforseo.com/v3/on_page/lighthouse/languages/)*
#### List of Languages for OnPage Lighthouse API

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/on_page/lighthouse/languages

You will receive the list of languages by calling this API.
 
As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the URL of the GET request* |
| ** `result`** | array | *array of results* |
| `language_name` | string | *language name* |
| `language_code` | string | *language code according to [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Audits
*Source: [https://docs.dataforseo.com/v3/on_page/lighthouse/audits/](https://docs.dataforseo.com/v3/on_page/lighthouse/audits/)*
#### Audits in OnPage Lighthouse API

The OnPage Lighthouse API is based on Google’s open-source Lighthouse project and provides data on the quality of web pages.

[Lighthouse Audits](https://github.com/GoogleChrome/lighthouse/blob/master/docs/understanding-results.md#audits) are objects containing the results of the page quality tests run by Lighthouse. This endpoint will provide you with a list of titles available for Lighthouse Audits. You can obtain the results of certain audits by specifying the corresponding titles in your [Task POST](https://docs.dataforseo.com/v3/on_page/lighthouse/task_post) requests.

**OnPage Lighthouse API is based on an open-source Lighthouse project. [You can find the official documentation here.](https://github.com/GoogleChrome/lighthouse/blob/master/readme.md)**

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/on_page/lighthouse/audits

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| ** `result`** | array | *array of results* |
| `audits` | array | *the list of available lighthouse audits*<br>an array containing the titles of available audits;<br>**Note:** the titles can change depending on if the audit passed or failed and may contain markdown code;<br>**Note #2:** if you’re using the audit that contains a slash (`/`) in its name, search by the last word after the slash |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The list of available audits:

---


#### Versions
*Source: [https://docs.dataforseo.com/v3/on_page/lighthouse/versions/](https://docs.dataforseo.com/v3/on_page/lighthouse/versions/)*
#### Lighthouse versions supported in OnPage API

OnPage Lighthouse API is based on Google’s open-source Lighthouse project and provides data on the quality of web pages.

This endpoint will provide you with a list of versions available for Lighthouse API. You can obtain the results specific to a certain Lighthouse version by specifying its number in the [Task POST](https://docs.dataforseo.com/v3/on_page/lighthouse/task_post/) request.

**OnPage Lighthouse API is based on an open-source Lighthouse project. [You can find the official documentation here.](https://github.com/GoogleChrome/lighthouse/blob/master/readme.md)**

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/on_page/lighthouse/versions

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| ** `result`** | array | *array of results* |
| `available_versions` | array | *the list of supported lighthouse versions*<br>an array contains objects with the version number and a boolean indicating whether the version is used by default<br>**Note:** you can specify the version in the POST request to the OnPage Lighthouse API |
| `version` | string | *lighthouse version*<br> |
| `default` | boolean | *the version is used by default*<br>if `false`, the version is not used by default and should be specified in the corresponding field of the POST request if necessary |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The list of available versions:

---


#### Task POST
*Source: [https://docs.dataforseo.com/v3/on_page/lighthouse/task_post/](https://docs.dataforseo.com/v3/on_page/lighthouse/task_post/)*
#### Setting Lighthouse Tasks

The OnPage Lighthouse API is based on Google’s open-source Lighthouse project for measuring the quality of web pages and web apps.

Lighthouse measures the quality of web pages by running a series of individual tests for each specific feature or metric to produce a numeric score and generate a report. It can run audits for performance, accessibility, progressive web apps, SEO, and conformity with best practices. You can find the full list of OnPage Lighthouse API audits in the [Lighthouse Audits](https://docs.dataforseo.com/v3/on_page/lighthouse/audits/) section. The results of the Lighthouse run will help you to easily strengthen the audited page or web app.

**OnPage Lighthouse API is based on an open-source Lighthouse project. [You can find the official documentation here.](https://github.com/GoogleChrome/lighthouse/blob/master/readme.md)**

POSThttps://api.dataforseo.com/v3/on_page/lighthouse/task_post

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page/lighthouse-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). Task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, with each POST call containing no more than 100 tasks. If your POST call contains over 100 tasks, the tasks over this limit will return the `40006` error.

You can retrieve the results of completed tasks using the unique task identifier `id`. Alternatively, we can send them to you as soon as they are ready if you specify `pingback_url` when setting a task. Note that if your server doesn’t respond within 10 seconds, the connection will be aborted by timeout, and the task will be transferred to the [‘Tasks Ready’](https://docs.dataforseo.com/v3/on_page/lighthouse/tasks_ready/?php) list. The error code and message depend on your server’s configuration. See [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) to learn more about using pingbacks with DataForSEO APIs.

To get more information about the OnPage Lighthouse API configuration parameters, please refer to the [official documentation of the Lighthouse project.](https://github.com/GoogleChrome/lighthouse/blob/master/docs/understanding-results.md#audits)

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `url` | string | *target URL***required field**target page should be specified with its absolute URL (including http:// or https://)example:`[https://dataforseo.com/](https://dataforseo.com/)` |
| `for_mobile` | boolean | *applies mobile emulation*optional fieldif set to `true`, Lighthouse will use mobile device and screen emulation to test the page against mobile environmentif set to `false`, the results will be provided for desktopdefault value: `false` |
| `categories` | array | *categories of Lighthouse audits*optional fieldeach category is a collection of audits and audit groups that applies weighting and scoring to the section ([see official definition](https://github.com/GoogleChrome/lighthouse/blob/master/docs/architecture.md#auditreport-terminology))**if you ignore this field, we will return data for all categories unless you specify `audits`**use this field to get data for specific categories you indicate herepossible values:`seo`, `performance`, `best_practices`, `accessibility` |
| `audits` | array | *Lighthouse audits*optional fieldaudits are individual tests Lighthouse runs for each specific feature/optimization/metric to produce a numeric score ([see official definition](https://github.com/GoogleChrome/lighthouse/blob/master/docs/architecture.md#components--terminology))**if you ignore this field, we will return data for all audits**use this field to get data for specific audits you indicate here**note** that some audits do not belong to a specific category and are stand-alone page quality measurementsin general, there can be several use cases:1. if you ignore `categories`, you can use this field to get data for the specified audits onlyfor example, if you ignore `"categories"` and specify `"audits": ["metrics/cumulative-layout-shift","metrics/largest-contentful-paint","metrics/total-blocking-time"]`, you will get data only for these audits2. if you specify a category, you can use this field to additionally receive audits that do not belong to the category(-ies) you specifiedfor example, if you specify `"categories": ["seo"]` and `"audits": ["metrics/cumulative-layout-shift","metrics/largest-contentful-paint","metrics/total-blocking-time"]`, you will get only these audits under "performance" and all audits under "seo"you can get [the full list of possible audits here](https://docs.dataforseo.com/v3/on_page/lighthouse/audits/) |
| `version` | string | *lighthouse version*optional fieldyou can obtain the results specific to a certain Lighthouse version by specifying its numberthe list of available versions is available through the [Lighthouse Versions endpoint](https://docs.dataforseo.com/v3/on_page/lighthouse/versions/) |
| `language_name` | string | *lighthouse language name*optional fieldyou can receive the list of available languages of the search engine with their `language_name` by making a separate request to `[https://api.dataforseo.com/v3/on_page/lighthouse/languages](https://api.dataforseo.com/v3/on_page/lighthouse/languages)`default value:`English` |
| `language_code` | string | *lighthouse language code*optional fieldyou can receive the list of available languages of the search engine with their `language_code` by making a separate request to `[https://api.dataforseo.com/v3/on_page/lighthouse/languages](https://api.dataforseo.com/v3/on_page/lighthouse/languages)`default value:`en` |
| `custom_user_agent` | string | *custom user agent*optional fieldspecify the custom user agent used by the browser when running the Lighthouse audit;can be specified with up to 254 characters; |
| `browser_screen_width` | integer | *browser screen width*optional fieldset the screen width of the browser used for the Lighthouse audit to emulate a specific device;can be specified within the following range: `240–9999`; |
| `browser_screen_height` | integer | *browser screen height*optional fieldset the screen height of the browser used for the Lighthouse audit to emulate a specific device;can be specified within the following range: `240–9999`; |
| `browser_screen_scale_factor` | float | *browser screen scale factor*optional fieldset the device pixel ratio of the browser used for the Lighthouse audit;can be specified within the following range: `0.5–3`; |
| `browser_network_throttling_method` | string | *browser network throttling method*optional fielddefines the method used to apply throttling during the Lighthouse audit;possible vaules:`simulate` - calculates estimated performance metrics without applying explicit throttling;`devtools` - applies the throttling settings specified in `browser_network_throttling` and `browser_cpu_throttling_multiplier`;`provided` - uses the network conditions of the crawling environment; |
| `browser_cpu_throttling_multiplier` | float | *browser CPU throttling multiplier***required if `browser_network_throttling_method` is set to `devtools`;**set the CPU throttling multiplier to simulate device performance conditions during the Lighthouse audit;can be specified within the following range: `1–4`;**Note:** this parameter is applied only when `browser_network_throttling_method` is set to `devtools`; |
| `browser_network_throttling` | string | *browser network throttling***required if `browser_network_throttling_method` is set to `devtools`;**set the network throttling profile to simulate connection speed conditions during the Lighthouse audit;possible values: `no_throttling`, `fast_4g`, `slow_4g`, `regular_3g`, `pc`;**Note:** this parameter is applied only when `browser_network_throttling_method` is set to `devtools`; |
| `tag` | string | *user-defined task identifier*optional field*the character limit is 255*you can use this parameter to identify the task and match it with the resultyou will find the specified `tag` value in the `data` object of the response |
| `pingback_url` | string | *notification URL of a completed task*optional fieldwhen a task is completed we will notify you by GET request sent to the URL you have specifiedyou can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request.example:`[http://your-server.com/pingscript?id=$id](http://your-server.com/pingscript?id=$id)``[http://your-server.com/pingscript?id=$id&tag=$tag](http://your-server.com/pingscript?id=$id&tag=$tag)`**Note:** special characters in `pingback_url` will be urlencoded;i.a., the `#` character will be encoded into `%23`learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task *generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| `result` | array | *array of results*in this case, the value will be `null` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Tasks Ready
*Source: [https://docs.dataforseo.com/v3/on_page/lighthouse/tasks_ready/](https://docs.dataforseo.com/v3/on_page/lighthouse/tasks_ready/)*
#### Get OnPage Lighthouse Completed Tasks

The **‘Tasks Ready’** endpoint is designed to provide you with the list of completed tasks, which haven’t been collected yet. If you use the Standard method without specifying the `postback_url`, you can receive the list of `id` for all completed tasks using this endpoint. Then, you can collect the results using the **‘Task GET’** endpoint.

Learn more about task completion and obtaining a list of completed tasks in [this help center article.](https://dataforseo.com/help-center/completed-tasks)

GEThttps://api.dataforseo.com/v3/on_page/lighthouse/tasks_ready

Pricing

Your account is not charged when receiving results

Each separate task will remain on the list until it is collected. You can make **up to 20 API calls per minute.** With each API call, you can get 1000 tasks completed within three previous days. The list will not contain the tasks which have already been collected and the tasks that were not collected **within the three days** after completion.

Please note that if you specify the `postback_url`, the task will not be in the list of completed tasks. The task can only be found in the list if the request to your server failed, and your server returned HTTP code response less than `200` or higher than `300`.

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the request’s URL* |
| ** `result`** | array | *array of results* |
| `id` | string | *task identifier of the completed task*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `tag` | string | *user-defined task identifier* |
| `endpoint_json` | string | *URL for collecting the results of the OnPage Lighthouse JSON task* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Task GET
*Source: [https://docs.dataforseo.com/v3/on_page/lighthouse/task_get/json/](https://docs.dataforseo.com/v3/on_page/lighthouse/task_get/json/)*
#### Get Lighthouse Results by ID

The OnPage Lighthouse API is based on Google’s open-source Lighthouse project for measuring the quality of web pages and web apps. This endpoint will provide you with the results of Lighthouse Audit. Use the `id` received in the response of your [Task POST](https://docs.dataforseo.com/v3/on_page/lighthouse/task_post/) request to get the results. The response will include data about all categories and audits specified in the Task POST. By default, the response will include all available data about the webpage including its performance, accessibility, progressive web apps, SEO, and compliance with best practices.

**Note:** if you’re using the audit that contains a slash (`/`) in its name, search the `audits` object by the last word after the slash;

**OnPage Lighthouse API is based on an open-source Lighthouse project. [You can find the official documentation here.](https://github.com/GoogleChrome/lighthouse/blob/master/readme.md)**

GEThttps://api.dataforseo.com/v3/on_page/lighthouse/task_get/json/$id

Pricing

Your account will be charged only for posting a task.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page/lighthouse-api) page.

**Description of the fields for sending a request:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *task identifier*<br>**required field**<br>you can get this ID in the response of the Task POST endpoint<br>example:<br>“07131248-1535-0216-1000-17384017ad04” |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| ** `result`** | array | *results of Lighthouse audit*<br>this array will include data according to the parameters specified in the POST request;<br>description of the fields in the `result` array is available in the [official documentation](https://github.com/GoogleChrome/lighthouse/blob/master/readme.md) |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Live
*Source: [https://docs.dataforseo.com/v3/on_page/lighthouse/live/json/](https://docs.dataforseo.com/v3/on_page/lighthouse/live/json/)*
#### Live OnPage Lighthouse JSON

The OnPage Lighthouse API is based on Google’s open-source Lighthouse project for measuring the quality of web pages and web apps.

Lighthouse measures the quality of web pages by running a series of individual tests for each specific feature or metric to produce a numeric score and generate a report. It can run audits for performance, accessibility, progressive web apps, SEO, and conformity with best practices. You can find the full list of OnPage Lighthouse API audits in the [Lighthouse Audits](https://docs.dataforseo.com/v3/on_page/lighthouse/audits/) section. The results of the Lighthouse run will help you to easily strengthen the audited page or web app.

**OnPage Lighthouse API is based on an open-source Lighthouse project. [You can find the official documentation here.](https://github.com/GoogleChrome/lighthouse/blob/master/readme.md)**

**Note:** if you’re using the audit that contains a slash (`/`) in its name, search the `audits` object by the last word after the slash

POSThttps://api.dataforseo.com/v3/on_page/lighthouse/live/json

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/on-page/lighthouse-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). Task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, with each POST call containing only one task.
The maximum number of simultaneous requests you can send is limited to 30.
Note that if Lighthouse cannot process a website within 120 seconds, the connection will be aborted by timeout.

To get more information about the OnPage Lighthouse API configuration parameters, please refer to the [official documentation of the Lighthouse project.](https://github.com/GoogleChrome/lighthouse/blob/master/docs/understanding-results.md#audits)

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `url` | string | *target URL***required field**target page should be specified with its absolute URL (including http:// or https://)example:`[https://dataforseo.com/](https://dataforseo.com/)` |
| `for_mobile` | bool | *applies mobile emulation*optional fieldif set to `true`, Lighthouse will use mobile device and screen emulation to test the page against mobile environmentif set to `false`, the results will be provided for desktopdefault value: `false` |
| `categories` | array | *categories of Lighthouse audits*optional fieldeach category is a collection of audits and audit groups that applies weighting and scoring to the section ([see official definition](https://github.com/GoogleChrome/lighthouse/blob/master/docs/architecture.md#auditreport-terminology))**if you ignore this field, we will return data for all categories unless you specify `audits`**use this field to get data for specific categories you indicate herepossible values:`seo`, `performance`, `best_practices`, `accessibility` |
| `audits` | array | *Lighthouse audits*optional fieldaudits are individual tests Lighthouse runs for each specific feature/optimization/metric to produce a numeric score ([see official definition](https://github.com/GoogleChrome/lighthouse/blob/master/docs/architecture.md#components--terminology)); **if you ignore this field, we will return data for all audits**;use this field to get data for specific audits you indicate here;**Note:** that some audits do not belong to a specific category and are stand-alone page quality measurements;in general, there can be several use cases:1. if you ignore `categories`, you can use this field to get data for the specified audits onlyfor example, if you ignore `"categories"` and specify `"audits": ["metrics/cumulative-layout-shift","metrics/largest-contentful-paint","metrics/total-blocking-time"]`, you will get data only for these audits2. if you specify a category, you can use this field to additionally receive audits that do not belong to the category(-ies) you specifiedfor example, if you specify `"categories": ["seo"]` and `"audits": ["metrics/cumulative-layout-shift","metrics/largest-contentful-paint","metrics/total-blocking-time"]`, you will get only these audits under "performance" and all audits under "seo"you can get [the full list of possible audits here](https://docs.dataforseo.com/v3/on_page/lighthouse/audits/) |
| `version` | string | *lighthouse version*optional fieldyou can obtain the results specific to a certain Lighthouse version by specifying its numberthe list of available versions is available through the [Lighthouse Versions endpoint](https://docs.dataforseo.com/v3/on_page/lighthouse/versions/) |
| `language_name` | string | *lighthouse language name*optional fieldyou can receive the list of available languages of the search engine with their `language_name` by making a separate request to `[https://api.dataforseo.com/v3/on_page/lighthouse/languages](https://api.dataforseo.com/v3/on_page/lighthouse/languages)`default value:`English` |
| `language_code` | string | *lighthouse language code*optional fieldyou can receive the list of available languages of the search engine with their `language_code` by making a separate request to `[https://api.dataforseo.com/v3/on_page/lighthouse/languages](https://api.dataforseo.com/v3/on_page/lighthouse/languages)`default value:`en` |
| `custom_user_agent` | string | *custom user agent*optional fieldspecify the custom user agent used by the browser when running the Lighthouse audit;can be specified with up to 254 characters; |
| `browser_screen_width` | integer | *browser screen width*optional fieldset the screen width of the browser used for the Lighthouse audit to emulate a specific device;can be specified within the following range: `240–9999`; |
| `browser_screen_height` | integer | *browser screen height*optional fieldset the screen height of the browser used for the Lighthouse audit to emulate a specific device;can be specified within the following range: `240–9999`; |
| `browser_screen_scale_factor` | float | *browser screen scale factor*optional fieldset the device pixel ratio of the browser used for the Lighthouse audit;can be specified within the following range: `0.5–3`; |
| `browser_network_throttling_method` | string | *browser network throttling method*optional fielddefines the method used to apply throttling during the Lighthouse audit;possible vaules:`simulate` - calculates estimated performance metrics without applying explicit throttling;`devtools` - applies the throttling settings specified in `browser_network_throttling` and `browser_cpu_throttling_multiplier`;`provided` - uses the network conditions of the crawling environment; |
| `browser_cpu_throttling_multiplier` | float | *browser CPU throttling multiplier***required if `browser_network_throttling_method` is set to `devtools`;**set the CPU throttling multiplier to simulate device performance conditions during the Lighthouse audit;can be specified within the following range: `1–4`;**Note:** this parameter is applied only when `browser_network_throttling_method` is set to `devtools`; |
| `browser_network_throttling` | string | *browser network throttling***required if `browser_network_throttling_method` is set to `devtools`;**set the network throttling profile to simulate connection speed conditions during the Lighthouse audit;possible values: `no_throttling`, `fast_4g`, `slow_4g`, `regular_3g`, `pc`;**Note:** this parameter is applied only when `browser_network_throttling_method` is set to `devtools`; |
| `tag` | string | *user-defined task identifier*optional field*the character limit is 255*you can use this parameter to identify the task and match it with the resultyou will find the specified `tag` value in the `data` object of the response |

 
As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified when setting a task<br>* |
| ** `result`** | array | *results of Lighthouse audit*<br>this array will include data according to the parameters you specified when setting a task;<br>all fields and their descriptions are available in the official documentation [by this link.](https://github.com/GoogleChrome/lighthouse/blob/master/readme.md) |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---
