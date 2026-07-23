# Backlinks API Documentation
*Consolidated main text documentation of Backlinks API compiled from docs.dataforseo.com*

---


### Overview
*Source: [https://docs.dataforseo.com/v3/backlinks/overview/](https://docs.dataforseo.com/v3/backlinks/overview/)*
### Backlinks API: Overview

Backlinks API is the power source of robust backlink data for domains, subdomains and webpages

Backlinks API is designed to be your flexible, fast, and reliable solution for getting quality data on inbound links, referring domains and referring pages for any domain, subdomain, or webpage. This API supplies data based on the live index. We crawl the web each second nonstop, so the stats you get are always up to the moment.

We’re continuously evolving our crawling infrastructure, enlarging our index, and enriching the datasets with new stats. You can always check up-to-the-moment volume of our backlink database by calling the [Index](https://docs.dataforseo.com/v3/backlinks/index) endpoint.

Backlinks API currently has the following set of mission-tailored endpoints that will supply you with a wealth of backlink data:

- [Summary](https://docs.dataforseo.com/v3/backlinks/summary/live/) will give you a complete backlink profile of the target.
- [History](https://docs.dataforseo.com/v3/backlinks/history/live/) will reveal the target’s past link-building performance.
- [Backlinks](https://docs.dataforseo.com/v3/backlinks/backlinks/live/) will return a detailed list of the target’s backlinks.
- [Anchors](https://docs.dataforseo.com/v3/backlinks/anchors/live/) will furnish you with the target’s anchor texts and stats.
- [Domain Pages](https://docs.dataforseo.com/v3/backlinks/domain_pages/live/) will uncover pages with the highest and lowest amount of backlinks.
- [Domain Pages Summary](https://docs.dataforseo.com/v3/backlinks/domain_pages_summary/live/) provides a summary of all backlinks and related metrics for each page of the target domain or subdomain.
- [Referring Domains](https://docs.dataforseo.com/v3/backlinks/referring_domains/live/) will provide backlink data broken down by domains pointing to the target.
- [Referring Networks](https://docs.dataforseo.com/v3/backlinks/referring_networks/live/) will uncover IP addresses and subnets that are sending backlinks to the target.
- [Competitors](https://docs.dataforseo.com/v3/backlinks/competitors/live/) will list competitors sharing a part of the backlink profile with the target.
- [Domain Intersection](https://docs.dataforseo.com/v3/backlinks/domain_intersection/live/) will list domains pointing to the specified targets.
- [Page Intersection](https://docs.dataforseo.com/v3/backlinks/page_intersection/live/) will list referring pages pointing to the specified targets.
- [Timeseries Summary](https://docs.dataforseo.com/v3/backlinks/timeseries_summary/live/) will provide backlink data for the target domain available during a period between the two indicated dates.
- [New & Lost Timeseries](https://docs.dataforseo.com/v3/backlinks/timeseries_new_lost_summary/live/) will provide the number of new and lost backlinks and referring domains for the specified target.

Using any endpoint, you can specify the number of results you want to retrieve, filter, and sort them. We do not charge any fees for using data filtering or sorting rules.

DataForSEO Backlinks API allows applying custom filtration to the dataset that will be retrieved. By using filters, you can effortlessly get exactly the data you need. For more information, please refer to the [Filters in the Backlinks API.](https://docs.dataforseo.com/v3/backlinks/filters/)

In addition to the endpoints listed above, Backlinks API also allows retrieving backlink stats for up to 1000 domains, subdomains, or pages. Using bulk endpoints, you can get:

- [Bulk Ranks](https://docs.dataforseo.com/v3/backlinks/bulk_ranks/live/)
- [Bulk Backlinks](https://docs.dataforseo.com/v3/backlinks/bulk_backlinks/live/)
- [Bulk Spam Score](https://docs.dataforseo.com/v3/backlinks/bulk_spam_score/live/)
- [Bulk Referring Domains](https://docs.dataforseo.com/v3/backlinks/bulk_referring_domains/live)
- [Bulk New & Lost Backlinks](https://docs.dataforseo.com/v3/backlinks/bulk_new_lost_backlinks/live/)
- [Bulk New & Lost Referring Domains](https://docs.dataforseo.com/v3/backlinks/bulk_new_lost_referring_domains/live/)

To find answers on common questions about DataForSEO Backlinks API and find guidance on efficient use of its features, [visit our Help Center.](https://dataforseo.com/help-center/category/backlinks-api)

##### Methods

DataForSEO Backlinks API supports only the Live method of data retrieval. It doesn’t require making separate POST and GET requests to the corresponding endpoints and delivers instant results. You can send up to 2000 API calls per minute. Contact us if you want to raise the limit.
Note that the maximum number of requests that can be sent simultaneously is limited to 30.

##### Cost

To use DataForSEO Backlinks API, you’ll need to [sign up for a Backlinks API access.](https://app.dataforseo.com/users/getrows)

**The amount you pay to gain access to Backlinks API is added to your account balance**, which you can spend on Backlinks API as well as any other DataForSEO API. Learn more about the pricing model of Backlinks API [in our help article.](https://dataforseo.com/help-center/backlinks-api-pricing-explained)

The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/backlinks/backlinks) page. You can check your spending in your [account dashboard](https://app.dataforseo.com/api-access) or by making a separate call to [the User Data endpoint.](https://docs.dataforseo.com/v3/appendix/user_data/?php)

You can test Backlinks API for free using DataForSEO [Sandbox.](https://docs.dataforseo.com/v3/appendix/sandbox/)

---


### Filters
*Source: [https://docs.dataforseo.com/v3/backlinks/filters/](https://docs.dataforseo.com/v3/backlinks/filters/)*
#### Filters available for DataForSEO Backlinks API

Backlinks API features plenty of parameters that support custom filtration. By applying filters to your POST requests, you will be able to effortlessly extract data that matches your requirements. Note that we do not charge any fees for using data filtering or sorting rules.

Here you will find all the necessary information about filters that can be used with DataForSEO Backlinks API endpoints.

Note that filters are associated with a certain object in the `result` array, and thus should be specified accordingly. You can learn more about how to use filters in [this help center article](https://dataforseo.com/help-center/using-filters).

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/backlinks/available_filters

You will receive the full list of filters by calling this API. You can also download the full list of possible filters [by this link.](https://cdn.dataforseo.com/v3/available_filters.php?api=backlinks)

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
| **`result`** | array | *array of results*<br>contains the full list of available parameters that can be used for data filtration<br>the parameters are grouped by the endpoint they can be used with |

Below you will find a detailed description of `filters` available in DataForSEO Backlinks API endpoints. You can specify up to 8 filters by using the `and`, `or` logical operators between the conditions.

**Note:** in [Domain Intersection](https://docs.dataforseo.com/v3/backlinks/domain_intersection/live) and [Page Intersection](https://docs.dataforseo.com/v3/backlinks/page_intersection/live) endpoints the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;
for example, if you specify the pages in the POST request as follows:
`"targets":[
"https://football.com/news",
"https://fifa.com/updates",
"https://uefa.com/updates"]
`
the specified pages will be assigned with sequence numbers; e.g. the filter by the “https://fifa.com/updates” page will be assigned a “2” and will look as follows:
`"filters": ["2.domain_from","=","news24.com"]`

**Note #2:** in [Backlinks Anchors](https://docs.dataforseo.com/v3/backlinks/anchors/live), [Domain Pages](https://docs.dataforseo.com/v3/backlinks/domain_pages/live) and [Domain Intersection](https://docs.dataforseo.com/v3/backlinks/domain_intersection/live) endpoints you may come across empty-titled fields in the `referring_links_semantic_locations` array, which, however, are also available in filters. These empty fields are denoted as `$empty` and have the `num` type.
example:
`referring_links_semantic_locations.$empty`

**Note #3:** in the following endpoints, you can filter the results by any top-level domain (TLD) from the `referring_links_tld` object of the response, but the structure of the filtered field is different:

• in [Backlinks Anchors](https://docs.dataforseo.com/v3/backlinks/anchors/live), [Referring Domains](https://docs.dataforseo.com/v3/backlinks/referring_domains/live), [Referring Networks](https://docs.dataforseo.com/v3/backlinks/referring_networks/live), and [Domain Pages Summary](https://docs.dataforseo.com/v3/backlinks/domain_pages_summary/live) endpoints, use `referring_links_tld.$tld`;
• in the [Domain Pages](https://docs.dataforseo.com/v3/backlinks/domain_pages/live) endpoint, use `page_summary.referring_links_tld.$tld`;
• in the [Domain Intersection](https://docs.dataforseo.com/v3/backlinks/domain_intersection/live) endpoint, use `$key.referring_links_tld.$tld`.

In all cases, replace the `$tld` variable with the necessary TLD returned in the `referring_links_tld` object of the endpoint’s response. Example filter:
`"filters": ["1.referring_links_tld.com",">",0]`

unlike other fields, `referring_links_tld.$tld` is only available in filters and cannot be used in the `order_by` parameter for sorting the results.

**Description of the available filters:**

| Field name | Type | Description |
| --- | --- | --- |
| `filters` | array | *array of results filtering parameters*<br>filters have the following structure:<br>**[`filered_field``filter_operator``filter_value`]**<br>**you can add several filters at once (8 filters maximum)**<br>if you add more than one filter, you must set a logical operator `and`, `or` between the conditions<br>example:<br>`[["domain_from","=", "dataforseo.com"],"and",[["acnhor","like","%seo%"],"or",["texr_pre","like","%seo%"]]]` |
| `filtered_field` | str | *fields that support filtration*<br>you can find all available `filtered_field` values [here](https://cdn.dataforseo.com/v3/available_filters.php?api=backlinks)<br>**Note:** fields with an `$empty` mark are empty, but their values can still be filtered;<br>in the fields containing `$key`, this variable denotes the sequence number of the target indicated in the `targets` array of the POST request |
| `filter_operator` | str | *operator in the filter*<br>available filter operators:<br>• if **`bool`**: `=`, `<>`<br>• if **`num`**: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>• if **`str`**: `match`, `not_match`, `like`, `not_like`, `ilike`, `not_ilike`, `in`, `not_in`, `=`, `<>`, `regex`, `not_regex`<br>• if **`array.str`**: `has`, `has_not`<br>• if **`array.num`**: `has`, `has_not`<br>• if **`time`**: `<`, `>``time` should be specified in the format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2021-01-29 15:02:37 +00:00`<br>if you specify `in` or `not_in` operator, the `$filter_value` should be specified as an array<br>example:<br>`["rank","in",[1,5]]`<br>`regex` and `not_regex` operators can be specified with `string` values using the [RE2 regex](https://github.com/google/re2/wiki/Syntax) syntax;<br>**Note:** the maximum limit for the number of characters you can specify in `regex` and `not_regex` is **1000**;<br>`like` and `not_like` operators require adding `%` symbol to get accurate results;<br>example:<br>`["anchor", "like", "%seo%"]` return `backlinks` items that contain “seo” in the `anchor` field<br>`["texr_pre", "not_like", "%seo%"]` do not return `backlinks` items that contain “seo” in the `text_pre` field |
| `filter_value` | | *filtering value*<br>values specified in the `filter_value` should match the format of the specified `filtered_field` |
| **filters available for the [backlinks](https://docs.dataforseo.com/v3/backlinks/backlinks/live) endpoint:** | | |
| `domain_from` | str | *domain referring to the target domain or webpage*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`<br>example:<br>`"filters": [["domain_from","like","forbes.%"],"and",["domain_from","<>","forbes.com"]]` |
| `url_from` | str | *URL of the page where the backlink is found*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`<br>example:<br>`"filters": [["domain_from","=","forbes.com"],"and",["url_from","like","%/sites/%"]]` |
| `url_from_https` | bool | *indicates whether the referring URL is secured with HTTPS*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["url_from_https","=",true]` |
| `domain_to` | str | *domain the backlink is pointing to*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`<br>example:<br>`"filters": [["domain_to","like","forbes.%"],"and",["domain_to","not_like","%forbes.com"]]` |
| `url_to` | str | *URL of the page the backlink is pointing to*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`<br>example:<br>`"filters": [["domain_to","=","forbes.com"],"and",["url_to","like","%/stories/collection%"]]` |
| `url_to_https` | bool | *indicates if the URL the backlink is pointing to is secured with HTTPS*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["url_to_https","=",false]` |
| `tld_from` | str | *top-level domain of the referring URL*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`<br>example:<br>`"filters": [["tld_from","=",".gov"],"or",["tld_from","=",".edu"]]` |
| `is_new` | bool | *indicates whether the backlink is new*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["is_new","=",true]` |
| `is_lost` | bool | *indicates whether the backlink was removed*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["is_lost","=",true]` |
| `backlink_spam_score` | num | *spam score of the backlink*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": [["backlink_spam_score","<", "10"]],"and",["backlink_spam_score",">","50"]]` |
| `rank` | num | *backlink rank*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": [["rank","<", "10"]],"and",["rank",">","1"]]` |
| `page_from_rank` | num | *page rank of the referring page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": [["page_from_rank","<", "10"]],"and",["page_from_rank",">","1"]]` |
| `domain_from_rank` | num | *domain rank of the referring domain*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": [["domain_from_rank","<", "10"]],"and",["domain_from_rank",">","1"]]` |
| `domain_from_platform_type` | array.str | *platform types of the referring domain*<br>the following operators are supported: `has`<br>example:<br>`"filters": ["domain_from_platform_type","has","blogs"]` |
| `domain_from_is_ip` | bool | *domain rank of the referring domain*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["domain_from_is_ip","=", false]` |
| `domain_from_ip` | str | *IP address of the referring domain*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`<br>example:<br>`"filters": [["domain_from_ip","=","172.64.32.57"],"or",["domain_from_ip","=","108.162.193.154"]]` |
| `page_from_external_links` | num | *number of external links found on the referring page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": [["page_from_external_links","<", "10"]],"and",["page_from_external_links",">","1"]]` |
| `page_from_internal_links` | num | *number of internal links found on the referring page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": [["page_from_internal_links","<", "10"]],"and",["page_from_internal_links",">","1"]]` |
| `page_from_size` | num | *size of the referring page, in bytes*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["page_from_page_from_size","<","63357"]` |
| `page_from_encoding` | str | *character encoding of the referring page*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`<br>example:<br>`"filters": ["page_from_encoding","=","utf-8"]` |
| `page_from_language` | str | *language of the referring page*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`<br>example:<br>`"filters": ["page_from_language","=","en"]` |
| `page_from_title` | str | *language of the referring page*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`<br>example:<br>`"filters": ["page_from_title","not_like","%seo%"]` |
| `page_from_status_code` | num | *HTTP status code returned by the referring page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": [["page_from_status_code","≥", "200"]],"and",["page_from_external_links","<","300"]]` |
| `first_seen` | time | *date and time when our crawler found the backlink for the first time*<br>in the [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) format<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["first_seen",">","2021-01-29 01:24:54 +00:00"]` |
| `prev_seen` | time | *previous to the most recent date when our crawler visited the backlink*<br>in the [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) format<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["prev_seen",">","2019-11-15 12:57:46 +00:00"]` |
| `last_seen` | time | *most recent date when our crawler visited the backlink*<br>in the [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) format<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["last_seen",">","2020-11-15 12:57:46 +00:00"]` |
| `item_type` | str | *link type*<br>possible values:<br>`anchor`, `image`, `meta`, `canonical`, `alternate`, `redirect`<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`<br>example:<br>`"filters": ["item_type","<>","redirect"]` |
| `dofollow` | bool | *indicates whether the backlink is dofollow*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["dofollow","=",true]` |
| `original` | bool | *indicates whether the backlink was present on the referring page when our crawler first visited it*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["original","=",false]` |
| `alt` | str | *alternative text of the image*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`<br>example:<br>`"filters": ["alt","like","%logo%"]` |
| `anchor` | str | *anchor text of the backlink*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`<br>example:<br>`"filters": ["anchor","like","%dataforseo%"]` |
| `text_pre` | str | *text snippet before the anchor text*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`<br>example:<br>`"filters": ["text_pre","like","%seo data provider%"]` |
| `text_post` | str | *text snippet after the anchor text*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`<br>example:<br>`"filters": ["text_post","like","%seo data provider%"]` |
| `semantic_location` | str | *indicates semantic element in HTML where the backlink is found*<br>you can get the full list of semantic elements [here](https://www.w3schools.com/html/html5_semantic_elements.asp)<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`<br>example:<br>`"filters": ["semantic_location","=","article"]` |
| `links_count` | num | *number of identical backlinks found on the referring page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["links_count","≥", "1"]` |
| `group_count` | num | *indicates total number of backlinks from this domain*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["group_count","≥", "5000"]` |
| `is_broken` | bool | *indicates whether the backlink is broken*<br>the following operators are supported: `=`, `<>`<br>example:<br>`"filters": ["is_broken","=",true]` |
| `url_to_status_code` | num | *status code of the referenced page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["url_to_status_code","=", "200"]` |
| `url_to_spam_score` | num | *spam score of the referenced page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": [["url_to_spam_score","<", "10"]],"and",["url_to_spam_score",">","50"]]` |
| **filters available for the [page intersection](https://docs.dataforseo.com/v3/backlinks/page_intersection/live) endpoint:** | | |
| `$key.domain_from` | str | *domain referring to the target domain or webpage*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`;<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>if you specify the pages in the POST request as follows:<br>`"targets":[<br>"https://football.com/news",<br>"https://fifa.com/updates",<br>"https://uefa.com/updates"`<br>the specified pages will be assigned with sequence numbers and the filter by the “https://fifa.com/updates” page will look as follows:<br>`"filters": ["2.domain_from","=","news24.com"]` |
| `$key.url_from` | str | *URL of the page where the backlink is found*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`;<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["2.url_from","=","https://news24.com/world-cup-2022"]<br>` |
| `$key.url_from` | str | *URL of the page where the backlink is found*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`;<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["2.url_from","=","https://news24.com/world-cup-2022"]<br>` |
| `$key.url_from_https` | bool | *indicates whether the referring URL is secured with HTTPS*<br>the following operators are supported: `=`, `<>`<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["2.url_from_https","=","true"]<br>` |
| `$key.domain_to` | str | *domain the backlink is pointing to*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`;<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": [["2.domain_to","<>","uefa.com"], "and", ["2.domain_to","<>","football.com"]]<br>` |
| `$key.url_to` | str | *URL the backlink is pointing to*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`;<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["2.url_to","<>","https://fifa.com/updates"]<br>` |
| `$key.url_to_https` | bool | *indicates if the URL the backlink is pointing to is secured with HTTPS*<br>the following operators are supported: `=`, `<>`<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["1.url_from_https","=","true"]<br>` |
| `$key.tld_from` | str | *top-level domain of the referring URL*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`;<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": [["1.tld_from","=","com"], "and", ["2.tld_from","=","com"], and, ["3.tld_from","=","com"]]<br>` |
| `$key.is_new` | bool | *indicates whether the backlink is new*<br>the following operators are supported: `=`, `<>`<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["1.is_new","=","true"]<br>` |
| `$key.is_lost` | bool | *indicates whether the backlink was removed*<br>the following operators are supported: `=`, `<>`<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["2.is_lost","<>","true"]<br>` |
| `$key.backlink_spam_score` | num | *spam score of the backlink*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": [["1.backlink_spam_score",">","80"]],"and",["2.backlink_spam_score","<","10"]]` |
| `$key.rank` | num | *backlink rank*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": [["1.rank",">","800"]],"and",["2.rank","<","100"]]` |
| `$key.page_from_rank` | num | *page rank of the referring page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": [["1.page_from_rank",">","800"]],"or",["2.page_from_rank",">","800"]]` |
| `$key.domain_from_rank` | num | *page rank of the referring domain*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": [["1.domain_from_rank",">","800"]],"or",["2.domain_from_rank",">","800"]]` |
| `domain_from_platform_type` | array.str | *platform types of the referring domain*<br>the following operators are supported: `has`<br>example:<br>`"filters": ["domain_from_platform_type","has","blogs"]` |
| `$key.domain_from_is_ip` | bool | *indicates if the domain is IP*<br>the following operators are supported: `=`, `<>`<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["2.domain_from_is_ip","=","false"]<br>` |
| `$key.domain_from_ip` | str | *IP address of the referring domain*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`;<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["1.domain_from_ip","like","%231.150"]<br>` |
| `$key.page_from_external_links` | num | *number of external links found on the referring page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": [["1.page_from_external_links",">","10"]],"or",["2.page_from_external_links",">","10"]]` |
| `$key.page_from_internal_links` | num | *number of internal links found on the referring page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["1.page_from_internal_links",">","50"]` |
| `$key.page_from_size` | num | *size of the referring page, in bytes*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["3.page_from_size","<","1000000"]` |
| `$key.page_from_encoding` | str | *character encoding of the referring page*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`;<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["3.page_from_encoding","like","utf-%"]<br>` |
| `$key.page_from_language` | str | *language of the referring page*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`;<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["3.page_from_language","=","de"]<br>` |
| `$key.page_from_title` | str | *title of the referring page*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`;<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["3.page_from_title","like","%world cup%"]<br>` |
| `$key.page_from_status_code` | num | *HTTP status code returned by the referring page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["3.page_from_status_code","=","200"]` |
| `$key.first_seen` | time | *date and time when our crawler found the backlink for the first time*<br>in the [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) format<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["1.first_seen",">","2021-01-29 01:24:54 +00:00"]` |
| `$key.prev_seen` | time | *previous to the most recent date when our crawler visited the backlink*<br>in the [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) format<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["2.prev_seen",">","2019-11-15 12:57:46 +00:00"]` |
| `$key.last_seen` | time | *most recent date when our crawler visited the backlink*<br>in the [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) format<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["3.last_seen",">","2020-11-15 12:57:46 +00:00"]` |
| `$key.item_type` | str | *link type*<br>possible values:<br>`anchor`, `image`, `link`, `meta`, `canonical`, `alternate`, `redirect`;<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`;<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["1.item_type","=","anchor"]<br>` |
| `$key.dofollow` | bool | *indicates whether the backlink is dofollow*<br>the following operators are supported: `=`, `<>`<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["1.dofollow","=","true"]<br>` |
| `$key.original` | bool | *indicates whether the backlink was present on the referring page when our crawler first visited it*<br>the following operators are supported: `=`, `<>`<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["1.original","=","true"]<br>` |
| `$key.alt` | str | *alternative text of the image*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`;<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["1.alt","like","%Gianni%"]<br>` |
| `$key.anchor` | str | *anchor text of the backlink*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`;<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["1.anchor","like","%FIFA%"]<br>` |
| `$key.text_pre` | str | *text snippet before the anchor text*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`;<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["1.text_pre","like","%Gianni%"]<br>` |
| `$key.text_post` | str | *text snippet after the anchor text*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`;<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["1.text_post","not_like","%Gianni%"]<br>` |
| `$key.semantic_location` | str | *indicates semantic element in HTML where the backlink is found*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`;<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["1.semantic_location","=","article"]<br>` |
| `$key.links_count` | num | *number of identical backlinks found on the referring page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["2.links_count",">","5"]` |
| `$key.group_count` | num | *indicates the total number of backlinks from this domain*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["2.group_count",">","100"]` |
| `$key.is_broken` | bool | *indicates whether the backlink is broken*<br>the following operators are supported: `=`, `<>`<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["2.is_broken","=","false"]<br>` |
| `$key.url_to_status_code` | num | *status code of the referenced page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["3.url_to_status_code","=","200"]` |
| `$key.url_to_spam_score` | num | *spam score of the referenced page*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>**Note:** the `$key` parameter refers to the variable denoting the sequence number of the page indicated in the `targets` array of the POST request;<br>example:<br>`"filters": ["3.url_to_spam_score",">","50"]` |

> The list of available filtration parameters:

---


### Index
*Source: [https://docs.dataforseo.com/v3/backlinks/index/](https://docs.dataforseo.com/v3/backlinks/index/)*
#### Backlinks Index

This endpoint will provide you with the total number of backlinks, domains, and pages our database contains for the moment when you make a request. You will also get stats for the last 12 months.

Note that monthly index data is available starting from 2021-10-01; subsequent months will be added over time.

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/backlinks/index

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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the URL of the GET request* |
| **`result`** | array | *array of results* |
| `total_backlinks` | integer | *total number of backlinks our database contains for the moment of checking* |
| `total_pages` | integer | *total number of pages our database contains for the moment of checking* |
| `total_domains` | integer | *total number of domains our database contains for the moment of checking* |
| `**index_history**` | array | *index volume data for the past 12 months* |
| `date` | string | *date for which index volume data is provided*<br>in the UTC format: “yyyy-mm-dd”<br>example:<br>`2021-10-01` |
| `total_backlinks` | integer | *total number of backlinks our database contained on the given `date`* |
| `total_pages` | integer | *total number of pages our database contained on the given `date`* |
| `total_domains` | integer | *total number of domains our database contained on the given `date`* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Summary
*Source: [https://docs.dataforseo.com/v3/backlinks/summary/live/](https://docs.dataforseo.com/v3/backlinks/summary/live/)*
#### Backlinks Summary

This endpoint will provide you with an overview of backlinks data available for a given domain, subdomain, or webpage.

POSThttps://api.dataforseo.com/v3/backlinks/summary/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/backlinks/backlinks) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. The maximum number of requests that can be sent simultaneously is limited to 30.

You can specify the number of results you want to retrieve, filter and sort them.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `target` | string | *domain, subdomain or webpage to get data for*<br>**required field**<br>a domain or a subdomain should be specified without `https://` and `www.`<br>a page should be specified with absolute URL (including `http://` or `https://`)<br> |
| `include_subdomains` | boolean | *indicates if the subdomains of the `target` will be included in the search*<br>optional field<br>if set to `false`, the subdomains will be ignored<br>default value: `true` |
| `include_indirect_links` | boolean | *indicates if indirect links to the `target` will be included in the results*<br>optional field<br>if set to `true`, the results will include data on indirect links pointing to a page that either redirects to the target, or points to a canonical page<br>if set to `false`, indirect links will be ignored<br>default value: `true` |
| `exclude_internal_backlinks` | boolean | *indicates if internal backlinks from subdomains to the `target` will be excluded from the results*<br>optional field<br>if set to `true`, the results will not include data on internal backlinks from subdomains of the same domain as `target`<br>if set to `false`, internal links will be included in the results<br>default value: `true` |
| `internal_list_limit` | integer | *maximum number of elements within internal arrays*<br>optional field<br>you can use this field to limit the number of elements within the following arrays:<br>`referring_links_tld`<br>`referring_links_types`<br>`referring_links_attributes`<br>`referring_links_platform_types`<br>`referring_links_semantic_locations`<br>default value: `10`<br>maximum value: `1000` |
| `backlinks_status_type` | string | *set what backlinks to return and count*<br>optional field<br>you can use this field to choose what backlinks will be returned and used for aggregated metrics for your `target`;<br>possible values:<br>`all` – all backlinks will be returned and counted;<br>`live` – backlinks found during the last check will be returned and counted;<br>`lost` – lost backlinks will be returned and counted;<br>default value: `live` |
| `backlinks_filters` | array | *filter the backlinks of your `target`*<br>optional field<br>you can use this field to filter the initial backlinks that will be included in the dataset for aggregated metrics for your `target`<br>you can filter the backlinks by all fields available in the response of [this endpoint](https://docs.dataforseo.com/v3/backlinks/backlinks/live)<br>using this parameter, you can include only dofollow backlinks in the response and create a flexible backlinks dataset to calculate the metrics for<br>example:<br>`"backlinks_filters": ["dofollow", "=", true]`<br> |
| `rank_scale` | string | *defines the scale used for calculating and displaying the `rank`, `domain_from_rank`, and `page_from_rank` values*<br>optional field<br>you can use this parameter to choose whether rank values are presented on a 0–100 or 0–1000 scale<br>possible values:<br>`one_hundred` — rank values are displayed on a 0–100 scale<br>`one_thousand` — rank values are displayed on a 0–1000 scale<br>default value: `one_thousand`<br>learn more about how this parameter works and how ranking metrics are calculated in [this Help Center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api#rank_scale) |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `target` | string | *`target` in a POST array* |
| `first_seen` | string | *date and time when our crawler found the backlink for the `target` for the first time*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `lost_date` | string | *date and time when the backlink was lost*<br>indicates the date and time when our crawler visited the target and it responded with a 4xx or 5xx status code or when its last backlink was removed<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `rank` | integer | `target` rank<br>learn more about the metric and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |
| `backlinks` | integer | *indicates the number of backlinks*<br> |
| `backlinks_spam_score` | integer | *spam score of the backlinks*<br>displays the total spam score of all backlinks pointing to the `target` domain, subdomain, or webpage;<br>to learn more about how the metric is calculated, refer to [this Help Center page](https://dataforseo.com/help-center/what-is-spam-score-and-how-is-it-calculated)<br> |
| `crawled_pages` | integer | *number of crawled pages for the `target`* |
| `info` | object | *information about the `target`* |
| `server` | string | *server* |
| `cms` | string | *content management system* |
| `platform_type` | array | *platform type* |
| `ip_address` | string | *IP address of the `target`* |
| `country` | string | *country code that the `target` domain is determined to belong to* |
| `is_ip` | boolean | *indicates if the `target` is IP*<br>if `true`, the domain, subdomain or webpage functions as an IP address and does not have a domain name |
| `target_spam_score` | integer | *spam score of the `target`*<br>if the `target` is a domain/subdomain, this fields indicates the average spam score of all pages of that domain/subdomain;<br>learn more about how the metric is calculated on [this help center page](https://dataforseo.com/help-center/what-is-spam-score-and-how-is-it-calculated) |
| `internal_links_count` | integer | *number of internal links*<br>calculated as the sum of internal links on the pages of the specified `target`<br> |
| `external_links_count` | integer | *number of external links on the page*<br>calculated as the sum of external links on the pages of the specified `target`<br> |
| `broken_backlinks` | integer | *number of broken backlinks*<br>number of broken backlinks pointing to the `target` |
| `broken_pages` | integer | *number of broken pages*<br>number of pages on the `target` that respond with 4xx or 5xx status codes<br>note that the number of broken pages includes pages on the `target` discovered by following external links, but it may also include pages discovered by following the target’s sitemap |
| `referring_domains` | integer | *indicates the number of referring domains*<br>referring domains include subdomains that are counted as separate domains for this metric<br> |
| `referring_domains_nofollow` | integer | *number of domains pointing at least one nofollow link to the `target`*<br> |
| `referring_main_domains` | integer | *indicates the number of referring main domains*<br> |
| `referring_main_domains_nofollow` | integer | *number of main domains pointing at least one nofollow link to the `target`* |
| `referring_ips` | integer | *number of referring IP addresses*<br>number of IP addresses pointing to this page<br> |
| `referring_subnets` | integer | *number of referring subnetworks*<br> |
| `referring_pages` | integer | *indicates the number of pages pointing to the target*<br> |
| `referring_links_tld` | object | *top-level domains of the referring links*<br>contains top level domains and referring link count per each<br> |
| `referring_links_types` | object | *types of referring links*<br>indicates the types of the referring links and link count per each type<br>possible values:<br>`anchor`, `image`, `link`, `meta`, `canonical`, `alternate`, `redirect`<br> |
| `referring_links_attributes` | object | *link attributes of the referring links*<br>indicates link attributes of the referring links and link count per each attribute<br>example values:<br>`nofollow`, `noopener`, `noreferrer`, `external`, `ugc`, `sponsored` |
| `referring_links_platform_types` | object | *types of referring platforms*<br>indicates referring platform types and and link count per each platform<br>possible values: `cms`, `blogs`, `ecommerce`, `message-boards`, `wikis`, `news`, `organization` |
| `referring_links_semantic_locations` | object | *semantic locations of the referring links*<br>indicates semantic elements in HTML where the referring links are located and link count per each semantic location<br>you can get the full list of semantic elements [here](https://www.w3schools.com/html/html5_semantic_elements.asp)<br>example values:<br>`article`, `section`, `summary`, `""` |
| `referring_links_countries` | object | *ISO country codes of the referring links*<br>indicates ISO country codes of the domains where the referring links are located and the link count per each country<br> |
| `referring_pages_nofollow` | integer | *number of referring pages pointing at least one nofollow link to the `target`* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Backlinks
*Source: [https://docs.dataforseo.com/v3/backlinks/backlinks/live/](https://docs.dataforseo.com/v3/backlinks/backlinks/live/)*
#### Backlinks

This endpoint will provide you with a list of backlinks and relevant data for the specified domain, subdomain, or webpage.

**Note:** API will return the list of unique backlinks from the referring pages;
if a page contains more than 1 backlink pointing to your `target`, the link with the highest `rank` will be returned; the number of duplicate backlinks from the referring page will be indicated in the `links_count` field.

POSThttps://api.dataforseo.com/v3/backlinks/backlinks/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/backlinks/backlinks) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. The maximum number of requests that can be sent simultaneously is limited to 30.

You can specify the number of results you want to retrieve, filter and sort them.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `target` | string | *domain, subdomain or webpage to get backlinks for*<br>**required field**<br>a domain or a subdomain should be specified without `https://` and `www.`<br>a page should be specified with absolute URL (including `http://` or `https://`) |
| `mode` | string | *results grouping type*<br>optional field<br>possible grouping types:<br>`as_is` – returns all backlinks<br>`one_per_domain` – returns one backlink per domain<br>`one_per_anchor` – returns one backlink per anchor<br>default value: `as_is` |
| `custom_mode` | object | *detailed results grouping type*<br>optional field<br>use this object to get a specific number of backlinks per `field`<br>if you use `custom_mode`, then `mode` will be ignored<br>example:<br>`"custom_mode": {"field": "domain", "value": 100}` |
| `filters` | array | *array of results filtering parameters*<br>optional field<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`=`, `<>`, `in`, `not_in`, `like`, `not_like`, `ilike`, `not_ilike`, `regex`, `not_regex`, `match`, `not_match`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>example:<br>`["rank",">","80"]`<br>`[["page_from_rank",">","55"],<br>"and",<br>["dofollow","=",true]]`<br>`[["first_seen",">","2017-10-23 11:31:45 +00:00"],<br>"and",<br>[["anchor","like","%seo%"],"or",["text_pre","like","%seo%"]]]`<br>The full list of possible filters is available [here.](https://docs.dataforseo.com/v3/backlinks/filters/?bash) |
| `order_by` | array | *results sorting rules*<br>optional field<br>you can use the same values as in the `filters` array to sort the results<br>possible sorting types:<br>`asc` – results will be sorted in the ascending order<br>`desc` – results will be sorted in the descending order<br>you should use a comma to set up a sorting type<br>example:<br>`["rank,desc"]`<br>**note that you can set no more than three sorting rules in a single request**<br>you should use a comma to separate several sorting rules<br>example:<br>`["domain_from_rank,desc","page_from_rank,asc"]` |
| `offset` | integer | *offset in the results array of the returned backlinks*<br>optional field<br>default value: `0`<br>if you specify the `10` value, the first ten backlinks in the results array will be omitted and the data will be provided for the successive backlinks;<br>**Note:** the maximum value is `20,000`, use the `search_after_token` if you would like to offset more results |
| `search_after_token` | string | *token for subsequent requests*<br>optional field<br>provided in the identical filed of the response to each request;<br>use this parameter to avoid timeouts while trying to obtain over `20,000` results in a single request;<br>by specifying the unique `search_after_token` value from the response array, you will get the subsequent results of the initial task;<br>`search_after_token` values are unique for each subsequent task ;<br>**Note:** if the `search_after_token` is specified in the request, all other parameters should be identical to the previous request |
| `limit` | integer | *the maximum number of returned backlinks*<br>optional field<br>default value: `100`<br>maximum value: `1000` |
| `backlinks_status_type` | string | *set what backlinks to return and count*<br>optional field<br>you can use this field to choose what backlinks will be returned and used for aggregated metrics for your `target`;<br>possible values:<br>`all` – all backlinks will be returned and counted;<br>`live` – backlinks found during the last check will be returned and counted;<br>`lost` – lost backlinks will be returned and counted;<br>default value: `live` |
| `include_subdomains` | boolean | *indicates if the subdomains of the `target` will be included in the search*<br>optional field<br>if set to `false`, the subdomains will be ignored<br>default value: `true` |
| `include_indirect_links` | boolean | *indicates if indirect links to the `target` will be included in the results*<br>optional field<br>if set to `true`, the results will include data on indirect links pointing to a page that either redirects to the target, or points to a canonical page<br>if set to `false`, indirect links will be ignored<br>default value: `true` |
| `exclude_internal_backlinks` | boolean | *indicates if internal backlinks from subdomains to the `target` will be excluded from the results*<br>optional field<br>if set to `true`, the results will not include data on internal backlinks from subdomains of the same domain as `target`<br>if set to `false`, internal links will be included in the results<br>default value: `true` |
| `rank_scale` | string | *defines the scale used for calculating and displaying the `rank`, `domain_from_rank`, and `page_from_rank` values*<br>optional field<br>you can use this parameter to choose whether rank values are presented on a 0–100 or 0–1000 scale<br>possible values:<br>`one_hundred` — rank values are displayed on a 0–100 scale<br>`one_thousand` — rank values are displayed on a 0–1000 scale<br>default value: `one_thousand`<br>learn more about how this parameter works and how ranking metrics are calculated in [this Help Center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api#rank_scale) |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `target` | string | *target domain in a POST array* |
| `mode` | string | *mode specified in a POST array* |
| `custom_mode` | object | *custom mode specified in a POST array* |
| `total_count` | integer | *total amount of results relevant the request* |
| `items_count` | integer | *the number of results returned in the `items` array* |
| `**items**` | array | *contains relevant backlinks and referring domains data* |
| `type` | string | * type of element = **‘backlink’*** |
| `domain_from` | string | *domain referring to the target domain or webpage* |
| `url_from` | string | *URL of the page where the backlink is found* |
| `url_from_https` | boolean | *indicates whether the referring URL is secured with HTTPS*<br>if `true`, the referring URL is secured with HTTPS |
| `domain_to` | string | *domain the backlink is pointing to* |
| `url_to` | string | *URL the backlink is pointing to* |
| `url_to_https` | boolean | *indicates if the URL the backlink is pointing to is secured with HTTPS*<br>if `true`, the URL is secured with HTTPS |
| `tld_from` | string | *top-level domain of the referring URL* |
| `is_new` | boolean | *indicates whether the backlink is new*<br>if `true`, the backlink was found on the page last time our crawler visited it |
| `is_lost` | boolean | *indicates whether the backlink was removed*<br>if `true`, the backlink or the entire page was removed |
| `backlink_spam_score` | integer | *spam score of the backlink*<br>learn more about how the metric is calculated on [this help center page](https://dataforseo.com/help-center/what-is-spam-score-and-how-is-it-calculated) |
| `rank` | integer | *backlink rank*<br>rank that the given backlink passes to the `target`<br>`rank` is calculated based on the method for node ranking in a linked database – a principle used in the original Google PageRank algorithm<br>learn more about the metric and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |
| `page_from_rank` | integer | *page rank of the referring page*<br>`page_from_rank` is calculated based on the method for node ranking in a linked database – a principle used in the original Google PageRank algorithm<br>learn more about the metric and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |
| `domain_from_rank` | integer | *domain rank of the referring domain*<br>`domain_from_rank` is calculated based on the method for node ranking in a linked database – a principle used in the original Google PageRank algorithm<br>learn more about the metric and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |
| `domain_from_platform_type` | array | *platform types of the referring domain*<br>possible values: `cms`, `blogs`, `ecommerce`, `message-boards`, `wikis`, `news`, `organization` |
| `domain_from_is_ip` | boolean | *indicates if the domain is IP*<br>if `true`, the domain functions as an IP address and does not have a domain name |
| `domain_from_ip` | string | *IP address of the referring domain* |
| `domain_from_country` | string | *ISO country code of the referring domain* |
| `page_from_external_links` | integer | *number of external links found on the referring page* |
| `page_from_internal_links` | integer | *number of internal links found on the referring page* |
| `page_from_size` | integer | *size of the referring page, in bytes*<br>example:<br>`63357` |
| `page_from_encoding` | string | *character encoding of the referring page*<br>example:<br>`utf-8` |
| `page_from_language` | string | *language of the referring page*<br>in ISO 639-1 format<br>example:<br>`en` |
| `page_from_title` | string | *title of the referring page* |
| `page_from_status_code` | integer | *HTTP status code returned by the referring page*<br>example:<br>`200` |
| `first_seen` | string | *date and time when our crawler found the backlink for the first time*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `prev_seen` | string | *previous to the most recent date when our crawler visited the backlink*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `last_seen` | string | *most recent date when our crawler visited the backlink*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `item_type` | string | *link type*<br>possible values:<br>`anchor`, `image`, `meta`, `canonical`, `alternate`, `redirect` |
| `attributes` | array | *link attributes of the referring links*<br>example:<br>`nofollow` |
| `dofollow` | boolean | *indicates whether the backlink is dofollow*<br>if `false`, the backlink is nofollow |
| `original` | boolean | *indicates whether the backlink was present on the referring page when our crawler first visited it* |
| `alt` | string | *alternative text of the image*<br>this field will be `null` if backlink `type` is not image<br> |
| `image_url` | string | *URL of the image*<br>the URL leading to the image on the original resource or DataForSEO storage (in case the original source is not available)<br> |
| `anchor` | string | *anchor text of the backlink* |
| `text_pre` | string | *snippet before the anchor text* |
| `text_post` | string | *snippet after the anchor text* |
| `semantic_location` | string | *indicates semantic element in HTML where the backlink is found*<br>you can get the full list of semantic elements [here](https://www.w3schools.com/html/html5_semantic_elements.asp)<br>examples:<br>`article`, `section`, `summary` |
| `links_count` | integer | *number of identical backlinks found on the referring page* |
| `group_count` | integer | *indicates total number of backlinks from this domain*<br>for example, if `mode` is set to `one_per_domain`, this field will indicate the total number of backlinks coming from this domain |
| `is_broken` | boolean | *indicates whether the backlink is broken*<br>if `true`, the backlink is pointing to a page responding with a 4xx or 5xx status code |
| `url_to_status_code` | integer | *status code of the referenced page*<br>if the value is `null`, our crawler hasn’t yet visited the webpage the link is pointing to<br>example:<br>`200` |
| `url_to_spam_score` | integer | *spam score of the referenced page*<br>if the value is `null`, our crawler hasn’t yet visited the webpage the link is pointing to;<br>learn more about how the metric is calculated on [this help center page](https://dataforseo.com/help-center/what-is-spam-score-and-how-is-it-calculated) |
| `url_to_redirect_target` | string | *target url of the redirect*<br>target page the redirect is pointing to |
| `ranked_keywords_info` | object | *number of keywords for which the page is ranked in top search results*<br> |
| `page_from_keywords_count_top_3` | integer | *number of keywords for which the page is ranked in top 3 search results*<br> |
| `page_from_keywords_count_top_10` | integer | *number of keywords for which the page is ranked in top 10 search results*<br> |
| `page_from_keywords_count_top_100` | integer | *number of keywords for which the page is ranked in top 100 search results*<br> |
| `is_indirect_link` | boolean | *indicates whether the backlink is an indirect link*<br>if `true`, the backlink is an indirect link pointing to a page that either redirects to `url_to`, or points to a canonical page |
| `indirect_link_path` | array | *indirect link path*<br>indicates a URL or a sequence of URLs that lead to `url_to` |
| `type` | string | *indirect link type*<br>possible values: `redirect`, `canonical` |
| `status_code` | integer | *HTTP status code of the URL* |
| `url` | string | *indirect link URL* |
| `search_after_token` | string | *token for subsequent requests*<br>by specifying the unique `search_after_token` when setting a new task, you will get the subsequent results of the initial task;<br>`search_after_token` values are unique for each subsequent task |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### History
*Source: [https://docs.dataforseo.com/v3/backlinks/history/live/](https://docs.dataforseo.com/v3/backlinks/history/live/)*
#### Backlinks History

This endpoint will provide you with historical backlinks data back to the beginning of 2019. You can receive the number of backlinks a given domain had in a specific time period, the number of new & lost backlinks, referring domains, and more.

Historical data is available from `2019-01-01`.

POSThttps://api.dataforseo.com/v3/backlinks/history/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/backlinks/backlinks) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute.

You can specify the time range, and we will provide historical backlink data within the set period.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `target` | string | *domain*<br>**required field**<br>a domain should be specified without `https://` and `www.` |
| `date_from` | string | *starting date of the time range*<br>optional field<br>minimum value `2019-01-01`<br>if you don’t specify this field, the minimum value will be used by default<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2019-01-15"` |
| `date_to` | string | *ending date of the time range*<br>optional field<br>if you don’t specify this field, the today’s date will be used by default<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2019-01-15"` |
| `rank_scale` | string | *defines the scale used for calculating and displaying the `rank`, `domain_from_rank`, and `page_from_rank` values*<br>optional field<br>you can use this parameter to choose whether rank values are presented on a 0–100 or 0–1000 scale<br>possible values:<br>`one_hundred` — rank values are displayed on a 0–100 scale<br>`one_thousand` — rank values are displayed on a 0–1000 scale<br>default value: `one_thousand`<br>learn more about how this parameter works and how ranking metrics are calculated in [this Help Center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api#rank_scale) |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `target` | string | *`target` from the POST array* |
| `date_from` | string | *starting date of the time range*<br>in the UTC format: “yyyy-mm-dd”<br>example:<br>`2019-01-01` |
| `date_to` | string | *ending date of the time range*<br>in the UTC format: `"yyyy-mm-dd"`<br>example:<br>`"2019-01-15"` |
| `items_count` | integer | *the number of results returned in the `items` array* |
| `**items**` | array | *contains historical backlink data for the specified domain*<br>the data is provided month-by-month;<br>the metrics are aggregated according to the backlinks the specified domain had on the first day of each given month |
| `type` | string | *type of element = **‘backlinks_history’*** |
| `date` | string | *date and time when the data for the target was stored*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br> |
| `rank` | integer | *domain rank on the given `date`*<br>learn more about the metric and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |
| `backlinks` | integer | *number of backlinks* |
| `new_backlinks` | integer | *number of new backlinks for the `target`*<br>data is provided based in a comparison with the previous period<br>**Note:** this data is available from May 2021;<br>if the date range specified in the POST request precedes May 2021, the field will equal `0` |
| `lost_backlinks` | integer | *number of lost backlinks for the `target`*<br>data is provided based in a comparison with the previous period<br>**Note:** this data is available from May 2021;<br>if the date range specified in the POST request precedes May 2021, the field will equal `0`<br> |
| `new_referring_domains` | integer | *number of new referring domains for the `target`*<br>data is provided based in a comparison with the previous period<br>**Note:** this data is available from May 2021;<br>if the date range specified in the POST request precedes May 2021, the field will equal `0`<br> |
| `lost_referring_domains` | integer | *number of lost referring domains for the `target`*<br>data is provided based in a comparison with the previous period<br>**Note:** this data is available from May 2021;<br>if the date range specified in the POST request precedes May 2021, the field will equal `0`<br> |
| `crawled_pages` | integer | *number of crawled pages for the `target`* |
| `info` | object | *information about the `target`* |
| `server` | string | *server* |
| `cms` | string | *content management system* |
| `platform_type` | array | *platform type* |
| `ip_address` | string | *IP address of the `target`* |
| `country` | string | *country code that the `target` domain is determined to belong to* |
| `is_ip` | boolean | *indicates if the `target` is IP*<br>if `true`, the domain, subdomain or webpage functions as an IP address and does not have a domain name |
| `target_spam_score` | integer | *spam score of the `target`*<br>if the `target` is a domain/subdomain, this fields indicates the average spam score of all pages of that domain/subdomain;<br>learn more about how the metric is calculated on [this help center page](https://dataforseo.com/help-center/what-is-spam-score-and-how-is-it-calculated) |
| `internal_links_count` | integer | *number of internal links*<br>calculated as the sum of internal links on the pages of the specified `target` |
| `external_links_count` | integer | *number of external links on the page*<br>calculated as the sum of external links on the pages of the specified `target` |
| `broken_backlinks` | integer | *number of broken backlinks*<br>number of broken backlinks pointing to the `target` |
| `broken_pages` | integer | *number of broken pages*<br>number of pages that receive backlinks but respond with 4xx or 5xx status codes |
| `referring_domains` | integer | *number of referring domains*<br>referring domains include subdomains that are counted as separate domains for this metric |
| `referring_domains_nofollow` | integer | *number of domains pointing at least one nofollow link to the `target`*<br> |
| `referring_main_domains` | integer | *number of referring main domains* |
| `referring_main_domains_nofollow` | integer | *number of main domains pointing at least one nofollow link to the `target`* |
| `referring_ips` | integer | *number of referring IP addresses*<br>number of IP addresses pointing to this page |
| `referring_subnets` | integer | *number of referring subnetworks* |
| `referring_pages` | integer | *number of pages pointing to the `target`* |
| `referring_links_tld` | object | *top-level domains of the referring links*<br>contains top-level domains and referring link count per each |
| `referring_links_types` | object | *types of referring links*<br>indicates the types of the referring links and link count per each type<br>possible values:<br>`anchor`, `image`, `link`, `meta`, `canonical`, `alternate`, `redirect` |
| `referring_links_attributes` | object | *link attributes of the referring links*<br>indicates link attributes of the referring links and link count per each attribute |
| `referring_links_platform_types` | object | *types of referring platforms*<br>indicates referring platform types and and link count per each platform<br>possible values: `cms`, `blogs`, `ecommerce`, `message-boards`, `wikis`, `news`, `organization` |
| `referring_links_semantic_locations` | object | *semantic locations of the referring links*<br>indicates semantic elements in HTML where the referring links are located and link count per each semantic location<br>you can get the full list of semantic elements [here](https://www.w3schools.com/html/html5_semantic_elements.asp)<br>examples:<br>`article`, `section`, `summary` |
| `referring_links_countries` | object | *ISO country codes of the referring links*<br>indicates ISO country codes of the domains where the referring links are located and the link count per each country<br> |
| `referring_pages_nofollow` | integer | *number of referring pages pointing at least one nofollow link to the `target`* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Anchors
*Source: [https://docs.dataforseo.com/v3/backlinks/anchors/live/](https://docs.dataforseo.com/v3/backlinks/anchors/live/)*
#### Anchors

This endpoint will provide you with a detailed overview of anchors used when linking to the specified website with relevant backlink data for each of them.

POSThttps://api.dataforseo.com/v3/backlinks/anchors/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/backlinks/backlinks) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `target` | string | *domain, subdomain or webpage to get anchors for*<br>**required field**<br>a domain or a subdomain should be specified without `https://` and `www.`<br>a page should be specified with absolute URL (including `http://` or `https://`) |
| `limit` | integer | *the maximum number of returned anchors*<br>optional field<br>default value: `100`<br>maximum value: `1000` |
| `offset` | integer | *offset in the results array of returned anchors*<br>optional field<br>default value: `0`<br>if you specify the `10` value, the first ten anchors in the results array will be omitted and the data will be provided for the successive anchors |
| `internal_list_limit` | integer | *maximum number of elements within internal arrays*<br>optional field<br>you can use this field to limit the number of elements within the following arrays:<br>`referring_links_tld`<br>`referring_links_types`<br>`referring_links_attributes`<br>`referring_links_platform_types`<br>`referring_links_semantic_locations`<br>default value: `10`<br>maximum value: `1000` |
| `backlinks_status_type` | string | *set what backlinks to return and count*<br>optional field<br>you can use this field to choose what backlinks will be returned and used for aggregated metrics for your `target`;<br>possible values:<br>`all` – all backlinks will be returned and counted;<br>`live` – backlinks found during the last check will be returned and counted;<br>`lost` – lost backlinks will be returned and counted;<br>default value: `live` |
| `filters` | array | *array of results filtering parameters*<br>optional field<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`regex`, `not_regex`, `=`, `<>`, `in`, `not_in`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>example:<br>`["referring_links_types.anchors",">","1"]`<br>`[["broken_pages",">","2"],<br>"and",<br>["backlinks",">","10"]]`<br>`[["first_seen",">","2017-10-23 11:31:45 +00:00"],<br>"and",<br>[["anchor","like","%seo%"],"or",["referring_domains",">","10"]]]`<br>The full list of possible filters is available [here.](https://docs.dataforseo.com/v3/backlinks/filters/?bash) |
| `order_by` | array | *results sorting rules*<br>optional field<br>you can use the same values as in the `filters` array to sort the results<br>possible sorting types:<br>`asc` – results will be sorted in the ascending order<br>`desc` – results will be sorted in the descending order<br>you should use a comma to set up a sorting type<br>example:<br>`["backlinks,desc"]`<br>**note that you can set no more than three sorting rules in a single request**<br>you should use a comma to separate several sorting rules<br>example:<br>`["backlinks,desc","rank,asc"]` |
| `backlinks_filters` | array | *filter the backlinks of your `target`*<br>optional field<br>you can use this field to filter the initial backlinks that will be included in the dataset for aggregated metrics for your `target`<br>you can filter the backlinks by all fields available in the response of [this endpoint](https://docs.dataforseo.com/v3/backlinks/backlinks/live/)<br>using this parameter, you can include only dofollow backlinks in the response and create a flexible backlinks dataset to calculate the metrics for<br>example:<br>`"backlinks_filters": [["dofollow", "=", true]]`<br> |
| `include_subdomains` | boolean | *indicates if the subdomains of the `target` will be included in the search*<br>optional field<br>if set to `false`, the subdomains will be ignored<br>default value: `true` |
| `include_indirect_links` | boolean | *indicates if indirect links to the `target` will be included in the results*<br>optional field<br>if set to `true`, the results will include data on indirect links pointing to a page that either redirects to the target, or points to a canonical page<br>if set to `false`, indirect links will be ignored<br>default value: `true` |
| `exclude_internal_backlinks` | boolean | *indicates whether the backlinks from subdomains of the `target` are excluded*<br>optional field<br>if set to `false`, the backlinks from subdomains of the `target` will be ommited and you won’t receive the same domain in the response;<br>default value: `true` |
| `rank_scale` | string | *defines the scale used for calculating and displaying the `rank`, `domain_from_rank`, and `page_from_rank` values*<br>optional field<br>you can use this parameter to choose whether rank values are presented on a 0–100 or 0–1000 scale<br>possible values:<br>`one_hundred` — rank values are displayed on a 0–100 scale<br>`one_thousand` — rank values are displayed on a 0–1000 scale<br>default value: `one_thousand`<br>learn more about how this parameter works and how ranking metrics are calculated in [this Help Center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api#rank_scale) |
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
| `target` | string | *target in the post array*<br> |
| `total_count` | integer | *total number of relevant items in the database*<br> |
| `items_count` | integer | *number of items in the results array*<br> |
| **`items`** | array | *items array*<br> |
| `type` | string | * type of element = **‘backlinks_anchor’*** |
| `anchor` | string | *anchor of the backlink* |
| `rank` | integer | *rank of the anchor links*<br>rank volume that referring websites pass to the `target` through links with a particular anchor<br>`rank` is calculated based on the method for node ranking in a linked database – a principle used in the original Google PageRank algorithm<br>learn more about the metric and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |
| `backlinks` | integer | *indicates the number of backlinks*<br> |
| `first_seen` | string | *date and time when our crawler found the backlink with this anchor for the first time*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `lost_date` | string | *date and time when the last backlink with this anchor was lost*<br>indicates the date and time when our crawler visited the page and it responded with 4xx or 5xx status code or the last backlink was removed<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2017-01-24 13:20:59 +00:00` |
| `backlinks_spam_score` | integer | *average spam score of all backlinks with this anchor*<br>learn more about how the metric is calculated on [this help center page](https://dataforseo.com/help-center/what-is-spam-score-and-how-is-it-calculated) |
| `broken_backlinks` | integer | *number of broken backlinks*<br>number of broken backlinks pointing to the `target` |
| `broken_pages` | integer | *number of broken pages*<br>number of pages that respond with 4xx or 5xx status codes where backlinks are pointing to<br> |
| `referring_domains` | integer | *indicates the number of referring domains*<br> |
| `referring_domains_nofollow` | integer | *number of domains pointing at least one nofollow link to the `target`*<br> |
| `referring_main_domains` | integer | *indicates the number of referring main domains*<br> |
| `referring_main_domains_nofollow` | integer | *number of main domains pointing at least one nofollow link to the `target`* |
| `referring_ips` | integer | *number of referring IP addresses*<br>number of IP addresses pointing to this page<br> |
| `referring_subnets` | integer | *number of referring subnetworks*<br> |
| `referring_pages` | integer | *indicates the number of pages pointing to `target` with this anchor*<br> |
| `referring_links_tld` | object | *top-level domains of the referring links*<br>contains top level domains and referring link count per each<br> |
| `referring_links_types` | object | *types of referring links*<br>indicates the types of the referring links and link count per each type<br>possible values:<br>`anchor`, `image`, `link`, `meta`, `canonical`, `alternate`, `redirect`<br> |
| `referring_links_attributes` | object | *link attributes of the referring links*<br>indicates link attributes of the referring links and link count per each attribute<br> |
| `referring_links_platform_types` | object | *types of referring platforms*<br>indicates referring platform types and and link count per each platform<br>possible values: `cms`, `blogs`, `ecommerce`, `message-boards`, `wikis`, `news`, `organization` |
| `referring_links_semantic_locations` | object | *semantic locations of the referring links*<br>indicates semantic elements in HTML where the referring links are located and link count per each semantic location<br>you can get the full list of semantic elements [here](https://www.w3schools.com/html/html5_semantic_elements.asp)<br>examples:<br>`article`, `section`, `summary` |
| `referring_links_countries` | object | *ISO country codes of the referring links*<br>indicates ISO country codes of the domains where the referring links are located and the link count per each country<br> |
| `referring_pages_nofollow` | integer | *number of referring pages pointing at least one nofollow link to the `target` with this anchor* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Referring Domains
*Source: [https://docs.dataforseo.com/v3/backlinks/referring_domains/live/](https://docs.dataforseo.com/v3/backlinks/referring_domains/live/)*
#### Referring Domains

This endpoint will provide you with a detailed overview of referring domains pointing to the target you specify.

POSThttps://api.dataforseo.com/v3/backlinks/referring_domains/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/backlinks/backlinks) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `target` | string | *domain, subdomain or webpage to get referring domains for*<br>**required field**<br>a domain or a subdomain should be specified without `https://` and `www.`<br>a page should be specified with absolute URL (including `http://` or `https://`) |
| `limit` | integer | *the maximum number of returned domains*<br>optional field<br>default value: `100`<br>maximum value: `1000` |
| `offset` | integer | *offset in the results array of returned domains*<br>optional field<br>default value: `0`<br>if you specify the `10` value, the first ten domains in the results array will be omitted and the data will be provided for the successive pages |
| `internal_list_limit` | integer | *maximum number of elements within internal arrays*<br>optional field<br>you can use this field to limit the number of elements within the following arrays:<br>`referring_links_tld`<br>`referring_links_types`<br>`referring_links_attributes`<br>`referring_links_platform_types`<br>`referring_links_semantic_locations`<br>default value: `10`<br>maximum value: `1000` |
| `backlinks_status_type` | string | *set what backlinks to return and count*<br>optional field<br>you can use this field to choose what backlinks will be returned and used for aggregated metrics for your `target`;<br>possible values:<br>`all` – all backlinks will be returned and counted;<br>`live` – backlinks found during the last check will be returned and counted;<br>`lost` – lost backlinks will be returned and counted;<br>default value: `live` |
| `filters` | array | *array of results filtering parameters*<br>optional field<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`regex`, `not_regex`, `=`, `<>`, `in`, `not_in`, `like`, `not_like`, `match`, `not_match`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>example:<br>`["referring_pages",">","1"]`<br>`[["referring_pages",">","2"],<br>"and",<br>["backlinks",">","10"]]`<br>`[["first_seen",">","2017-10-23 11:31:45 +00:00"],<br>"and",<br>[["domain","like","%dataforseo.com%"],"or",["referring_domains",">","10"]]]`<br>The full list of possible filters is available [here.](https://docs.dataforseo.com/v3/backlinks/filters/?bash) |
| `order_by` | array | *results sorting rules*<br>optional field<br>you can use the same values as in the `filters` array to sort the results<br>possible sorting types:<br>`asc` – results will be sorted in the ascending order<br>`desc` – results will be sorted in the descending order<br>you should use a comma to set up a sorting type<br>example:<br>`["backlinks,desc"]`<br>**note that you can set no more than three sorting rules in a single request**<br>you should use a comma to separate several sorting rules<br>example:<br>`["backlinks,desc","rank,asc"]` |
| `backlinks_filters` | array | *filter the backlinks of your `target`*<br>optional field<br>you can use this field to filter the initial backlinks that will be included in the dataset for aggregated metrics for your `target`<br>you can filter the backlinks by all fields available in the response of [this endpoint](https://docs.dataforseo.com/v3/backlinks/backlinks/live)<br>using this parameter, you can include only dofollow backlinks in the response and create a flexible backlinks dataset to calculate the metrics for<br>example:<br>`"backlinks_filters": ["dofollow", "=", true]`<br> |
| `include_subdomains` | boolean | *indicates if the subdomains of the `target` will be included in the search*<br>optional field<br>if set to `false`, the subdomains will be ignored<br>default value: `true` |
| `include_indirect_links` | boolean | *indicates if indirect links to the `target` will be included in the results*<br>optional field<br>if set to `true`, the results will include data on indirect links pointing to a page that either redirects to the target, or points to a canonical page<br>if set to `false`, indirect links will be ignored<br>default value: `true` |
| `exclude_internal_backlinks` | boolean | *indicates whether the backlinks from subdomains of the `target` are excluded*<br>optional field<br>if set to `false`, the backlinks from subdomains of the `target` will be ommited and you won’t receive the same domain in the response;<br>default value: `true` |
| `rank_scale` | string | *defines the scale used for calculating and displaying the `rank`, `domain_from_rank`, and `page_from_rank` values*<br>optional field<br>you can use this parameter to choose whether rank values are presented on a 0–100 or 0–1000 scale<br>possible values:<br>`one_hundred` — rank values are displayed on a 0–100 scale<br>`one_thousand` — rank values are displayed on a 0–1000 scale<br>default value: `one_thousand`<br>learn more about how this parameter works and how ranking metrics are calculated in [this Help Center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api#rank_scale) |
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
| `target` | string | *`target` in a POST array*<br> |
| `total_count` | integer | *total number of relevant items in the database*<br>total number of main domains referring to your target;<br>example.com and blog.example.com are counted as one referring domain |
| `items_count` | integer | *number of items in the `items` array*<br> |
| **`items`** | array | *items array*<br> |
| `type` | string | * type of element = **‘backlinks_referring_domain’*** |
| `domain` | string | *referring domain* |
| `rank` | integer | *domain rank*<br>rank volume that a referring website passes to the `target`<br>`rank` is calculated based on the method for node ranking in a linked database – a principle used in the original Google PageRank algorithm<br>learn more about the metric and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |
| `backlinks` | integer | *indicates the number of backlinks pointing to the `target`*<br> |
| `first_seen` | string | *date and time when our crawler found the backlink for the first time*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `lost_date` | string | *date and time when the last backlink from this domain was lost*<br>indicates the date and time when our crawler visited the page and it responded with 4xx or 5xx status code or the last backlink was removed<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2017-01-24 13:20:59 +00:00` |
| `backlinks_spam_score` | integer | *average spam score of all backlinks pointing to the domain*<br>learn more about how the metric is calculated on [this help center page](https://dataforseo.com/help-center/what-is-spam-score-and-how-is-it-calculated) |
| `broken_backlinks` | integer | *number of broken backlinks*<br>number of broken backlinks pointing to the domain<br> |
| `broken_pages` | integer | *number of broken pages*<br>number of pages that respond with 4xx or 5xx status codes where backlinks are pointing to<br> |
| `referring_domains` | integer | *indicates the number of referring domains*<br>note that we calculate main domains (root domains, like `example.com`) and their subdomains (e.g. `blog.example.com`) separately for this metric<br> |
| `referring_domains_nofollow` | integer | *number of domains pointing at least one nofollow link to the `target`*<br> |
| `referring_main_domains` | integer | *indicates the number of referring main domains*<br>the number of primary (root) domains referring to your target |
| `referring_main_domains_nofollow` | integer | *number of main domains pointing at least one nofollow link to the `target`* |
| `referring ips` | integer | *number of referring IP addresses*<br>number of IP addresses pointing to this page<br> |
| `referring subnets` | integer | *number of referring subnetworks*<br> |
| `referring_pages` | integer | *indicates the number of pages pointing to the `target` specified*<br> |
| `referring_links_tld` | object | *top-level domains of the referring links*<br>contains top level domains and referring link count per each<br> |
| `referring_links_types` | object | *types of referring links*<br>indicates the types of the referring links and link count per each type<br>possible values:<br>`anchor`, `image`, `link`, `meta`, `canonical`, `alternate`, `redirect`<br> |
| `referring_links_attributes` | object | *link attributes of the referring links*<br>indicates link attributes of the referring links and link count per each attribute<br> |
| `referring_links_platform_types` | object | *types of referring platforms*<br>indicates referring platform types and link count per each platform<br>possible values: `cms`, `blogs`, `ecommerce`, `message-boards`, `wikis`, `news`, `organization` |
| `referring_links_semantic_locations` | object | *semantic locations of the referring links*<br>indicates semantic elements in HTML where the referring links are located and the link count per each semantic location<br>you can get the full list of semantic elements [here](https://www.w3schools.com/html/html5_semantic_elements.asp)<br>examples:<br>`article`, `section`, `summary` |
| `referring_links_countries` | object | *ISO country codes of the referring links*<br>indicates ISO country codes of the domains where the referring links are located and the link count per each country<br> |
| `referring_pages_nofollow` | integer | *number of referring pages pointing at least one nofollow link to the `target`* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Referring Networks
*Source: [https://docs.dataforseo.com/v3/backlinks/referring_networks/live/](https://docs.dataforseo.com/v3/backlinks/referring_networks/live/)*
#### Referring Networks

This endpoint will provide you with a detailed overview of referring IPs and subnets pointing to the `target` you specify.

POSThttps://api.dataforseo.com/v3/backlinks/referring_networks/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/backlinks/backlinks) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `target` | string | *domain, subdomain or webpage to get referring networks for*<br>**required field**<br>a domain or a subdomain should be specified without `https://` and `www.`<br>a page should be specified with absolute URL (including `http://` or `https://`) |
| `network_address_type` | string | *indicates the type of network to get data for*<br>optional field<br>possible values: `ip`, `subnet`<br>default value: `ip` |
| `limit` | integer | *the maximum number of returned networks*<br>optional field<br>default value: `100`<br>maximum value: `1000` |
| `offset` | integer | *offset in the results array of returned networks*<br>optional field<br>default value: `0`<br>if you specify the `10` value, the first ten domains in the results array will be omitted and the data will be provided for the successive pages |
| `internal_list_limit` | integer | *maximum number of elements within internal arrays*<br>optional field<br>you can use this field to limit the number of elements within the following arrays:<br>`referring_links_tld`<br>`referring_links_types`<br>`referring_links_attributes`<br>`referring_links_platform_types`<br>`referring_links_semantic_locations`<br>default value: `10`<br>maximum value: `1000` |
| `backlinks_status_type` | string | *set what backlinks to return and count*<br>optional field<br>you can use this field to choose what backlinks will be returned and used for aggregated metrics for your `target`;<br>possible values:<br>`all` – all backlinks will be returned and counted;<br>`live` – backlinks found during the last check will be returned and counted;<br>`lost` – lost backlinks will be returned and counted;<br>default value: `live` |
| `filters` | array | *array of results filtering parameters*<br>optional field<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`regex`, `not_regex`, `=`, `<>`, `in`, `not_in`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>example:<br>`["referring_pages",">","1"]`<br>`[["referring_pages",">","2"],<br>"and",<br>["backlinks",">","10"]]`<br>`[["first_seen",">","2017-10-23 11:31:45 +00:00"],<br>"and",<br>[["network_address","like","194.1.%"],"or",["referring_ips",">","10"]]]`<br>The full list of possible filters is available [here.](https://docs.dataforseo.com/v3/backlinks/filters/?bash) |
| `order_by` | array | *results sorting rules*<br>optional field<br>you can use the same values as in the `filters` array to sort the results<br>possible sorting types:<br>`asc` – results will be sorted in the ascending order<br>`desc` – results will be sorted in the descending order<br>you should use a comma to set up a sorting type<br>example:<br>`["backlinks,desc"]`<br>**note that you can set no more than three sorting rules in a single request**<br>you should use a comma to separate several sorting rules<br>example:<br>`["backlinks,desc","rank,asc"]` |
| `backlinks_filters` | array | *filter the backlinks of your `target`*<br>optional field<br>you can use this field to filter the initial backlinks that will be included in the dataset for aggregated metrics for your `target`<br>you can filter the backlinks by all fields available in the response of [this endpoint](https://docs.dataforseo.com/v3/backlinks/backlinks/live)<br>using this parameter, you can include only dofollow backlinks in the response and create a flexible backlinks dataset to calculate the metrics for<br>example:<br>`"backlinks_filters": [["dofollow", "=", true]]`<br> |
| `include_subdomains` | boolean | *indicates if the subdomains of the `target` will be included in the search*<br>optional field<br>if set to `false`, the subdomains will be ignored<br>default value: `true` |
| `include_indirect_links` | boolean | *indicates if indirect links to the `target` will be included in the results*<br>optional field<br>if set to `true`, the results will include data on indirect links pointing to a page that either redirects to the target, or points to a canonical page<br>if set to `false`, indirect links will be ignored<br>default value: `true` |
| `exclude_internal_backlinks` | boolean | *indicates whether the backlinks from subdomains of the `target` are excluded*<br>optional field<br>if set to `false`, the backlinks from subdomains of the `target` will be ommited and you won’t receive the same domain in the response;<br>default value: `true` |
| `rank_scale` | string | *defines the scale used for calculating and displaying the `rank`, `domain_from_rank`, and `page_from_rank` values*<br>optional field<br>you can use this parameter to choose whether rank values are presented on a 0–100 or 0–1000 scale<br>possible values:<br>`one_hundred` — rank values are displayed on a 0–100 scale<br>`one_thousand` — rank values are displayed on a 0–1000 scale<br>default value: `one_thousand`<br>learn more about how this parameter works and how ranking metrics are calculated in [this Help Center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api#rank_scale) |
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
| `target` | string | *`target` in a POST array*<br> |
| `total_count` | integer | *total number of relevant items in the database*<br> |
| `items_count` | integer | *number of items in the `items` array*<br> |
| **`items`** | array | *items array*<br> |
| `type` | string | * type of element = **‘backlinks_referring_network’*** |
| `network_address` | string | *address of the referring subnetwork or IP* |
| `rank` | integer | *network rank*<br>rank volume that a referring network passes to the `target`<br>`rank` is calculated based on the method for node ranking in a linked database – a principle used in the original Google PageRank algorithm<br>learn more about the metric and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |
| `backlinks` | integer | *indicates the number of backlinks pointing to the `target`*<br> |
| `first_seen` | string | *date and time when our crawler found the backlink for the first time*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `lost_date` | string | *date and time when the last backlink from this domain was lost*<br>indicates the date and time when our crawler visited the page and it responded with 4xx or 5xx status code or the last backlink was removed<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2017-01-24 13:20:59 +00:00` |
| `broken_backlinks` | integer | *number of broken backlinks*<br>number of broken backlinks pointing to the domain<br> |
| `broken_pages` | integer | *number of broken pages*<br>number of pages that respond with 4xx or 5xx status codes where backlinks are pointing to<br> |
| `referring_domains` | integer | *indicates the number of referring domains*<br>referring domains include subdomains that are counted as separate domains for this metric<br> |
| `referring_domains_nofollow` | integer | *number of domains pointing at least one nofollow link to the `target`*<br> |
| `referring_main_domains` | integer | *indicates the number of referring main domains*<br> |
| `referring_main_domains_nofollow` | integer | *number of main domains pointing at least one nofollow link to the `target`* |
| `referring ips` | integer | *number of referring IP addresses*<br>number of IP addresses pointing to this page<br> |
| `referring subnets` | integer | *number of referring subnetworks*<br> |
| `referring_pages` | integer | *indicates the number of pages pointing to the `target` specified*<br> |
| `referring_links_tld` | object | *top-level domains of the referring links*<br>contains top level domains and referring link count per each<br> |
| `referring_links_types` | object | *types of referring links*<br>indicates the types of the referring links and link count per each type<br>possible values:<br>`anchor`, `image`, `link`, `meta`, `canonical`, `alternate`, `redirect`<br> |
| `referring_links_attributes` | object | *link attributes of the referring links*<br>indicates link attributes of the referring links and link count per each attribute<br> |
| `referring_links_platform_types` | object | *types of referring platforms*<br>indicates referring platform types and and link count per each platform<br>possible values: `cms`, `blogs`, `ecommerce`, `message-boards`, `wikis`, `news`, `organization` |
| `referring_links_semantic_locations` | object | *semantic locations of the referring links*<br>indicates semantic elements in HTML where the referring links are located and the link count per each semantic location<br>you can get the full list of semantic elements [here](https://www.w3schools.com/html/html5_semantic_elements.asp)<br>examples:<br>`article`, `section`, `summary` |
| `referring_links_countries` | object | *ISO country codes of the referring links*<br>indicates ISO country codes of the domains where the referring links are located and the link count per each country<br> |
| `referring_pages_nofollow` | integer | *number of referring pages pointing at least one nofollow link to the `target`* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Competitors
*Source: [https://docs.dataforseo.com/v3/backlinks/competitors/live/](https://docs.dataforseo.com/v3/backlinks/competitors/live/)*
#### Competitors

This endpoint will provide you with a list of competitors that share some part of the backlink profile with a target website, along with a number of backlink intersections and the rank of every competing website.

POSThttps://api.dataforseo.com/v3/backlinks/competitors/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/backlinks/backlinks) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `target` | string | *domain, subdomain or webpage to get competitor domains for*<br>**required field**<br>a domain or a subdomain should be specified without `https://` and `www.`<br>a page should be specified with absolute URL (including `http://` or `https://`) |
| `limit` | integer | *the maximum number of returned domains*<br>optional field<br>default value: `100`<br>maximum value: `1000` |
| `offset` | integer | *offset in the results array of returned domains*<br>optional field<br>default value: `0`<br>if you specify the `10` value, the first ten domains in the results array will be omitted and the data will be provided for the successive pages |
| `filters` | array | *array of results filtering parameters*<br>optional field<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`regex`, `not_regex`, `=`, `<>`, `in`, `not_in`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>example:<br>`["rank",">","100"]`<br>`[["target","like","%forbes%"],<br>"and",<br>[["rank",">","100"],"or",["intersections",">","5"]]]`<br>The full list of possible filters is available [here.](https://docs.dataforseo.com/v3/backlinks/filters/?bash) |
| `order_by` | array | *results sorting rules*<br>optional field<br>you can use the same values as in the `filters` array to sort the results<br>possible sorting types:<br>`asc` – results will be sorted in the ascending order<br>`desc` – results will be sorted in the descending order<br>you should use a comma to set up a sorting type<br>example:<br>`["rank,desc"]`<br>**note that you can set no more than three sorting rules in a single request**<br>you should use a comma to separate several sorting rules<br>example:<br>`["intersections,desc","rank,asc"]` |
| `main_domain` | boolean | *indicates if only main domain of the `target` will be included in the search*<br>optional field<br>if set to `true`, only the main domain will be included in search;<br>default value: `true` |
| `exclude_large_domains` | boolean | *indicates whether large domain will appear in results*<br>optional field<br>if set to `true`, the results from the large domain (google.com, amazon.com, etc.) will be omitted;<br>default value: `true` |
| `exclude_internal_backlinks` | boolean | *indicates if internal backlinks from subdomains to the `target` will be excluded from the results*<br>optional field<br>if set to `true`, the results will not include data on internal backlinks from subdomains of the same domain as `target`<br>if set to `false`, internal links will be included in the results<br>default value: `true` |
| `rank_scale` | string | *defines the scale used for calculating and displaying the `rank`, `domain_from_rank`, and `page_from_rank` values*<br>optional field<br>you can use this parameter to choose whether rank values are presented on a 0–100 or 0–1000 scale<br>possible values:<br>`one_hundred` — rank values are displayed on a 0–100 scale<br>`one_thousand` — rank values are displayed on a 0–1000 scale<br>default value: `one_thousand`<br>learn more about how this parameter works and how ranking metrics are calculated in [this Help Center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api#rank_scale) |
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
| `total_count` | integer | *total number of relevant items in the database*<br> |
| `items_count` | integer | *number of items in the `items` array*<br> |
| **`items`** | array | *items array*<br> |
| `type` | string | * type of element = **‘backlinks_competitors’*** |
| `target` | string | *competitor domain* |
| `rank` | integer | *domain rank*<br>domain rank across all domains in the database<br>`rank` is calculated based on the method for node ranking in a linked database – a principle used in the original Google PageRank algorithm<br>learn more about the metric and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |
| `intersections` | integer | *indicates the number of backlink intersections with the `target` specified in the POST array*<br> |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Domain Intersection
*Source: [https://docs.dataforseo.com/v3/backlinks/domain_intersection/live/](https://docs.dataforseo.com/v3/backlinks/domain_intersection/live/)*
#### Domain Intersection

This endpoint will provide you with the list of domains pointing to the specified websites. This endpoint is especially useful for creating a Link Gap feature that shows what domains link to your competitors but do not link out to your website.

POSThttps://api.dataforseo.com/v3/backlinks/domain_intersection/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/backlinks/backlinks) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. The maximum number of requests that can be sent simultaneously is limited to 30.

You can specify the number of results you want to retrieve, filter and sort them.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `targets` | object | *domains, subdomains or webpages to get links for*<br>**required field**<br>you can set up to 20 domains, subdomains or webpages<br>a domain or a subdomain should be specified without `https://` and `www.`<br>a page should be specified with absolute URL (including `http://` or `https://`)<br>example:<br>`"targets": {<br>"1": "http://planet.postgresql.org/",<br>"2": "http://gborg.postgresql.org/"<br>}` |
| `exclude_targets` | array | *domains, subdomains or webpages you want to exclude*<br>optional field<br>you can specify up to 10 domains, subdomains or webpages<br>if you use this array, results will contain the referring domains that link to `targets` but don’t link to `exclude_targets`<br>example:<br>`"exclude_targets": [<br>"bbc.com",<br>"https://www.apple.com/iphone/*",<br>"https://dataforseo.com/apis/*"]`<br> |
| `filters` | array | *array of results filtering parameters*<br>optional field<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`regex`, `not_regex`, `=`, `<>`, `in`, `not_in`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>example:<br>`["1.internal_links_count",">","1"]`<br>`[["2.referring_pages",">","2"],<br>"and",<br>["1.backlinks",">","10"]]`<br>`[["1.first_seen",">","2017-10-23 11:31:45 +00:00"],<br>"and",<br>[["2.target","like","%dataforseo.com%"],"or",["1.referring_domains",">","10"]]]`<br>The full list of possible filters is available [here.](https://docs.dataforseo.com/v3/backlinks/filters/?bash) |
| `order_by` | array | *results sorting rules*<br>optional field<br>you can use the same values as in the `filters` array to sort the results<br>possible sorting types:<br>`asc` – results will be sorted in the ascending order<br>`desc` – results will be sorted in the descending order<br>you should use a comma to set up a sorting type<br>example:<br>`["backlinks,desc"]`<br>**note that you can set no more than three sorting rules in a single request**<br>you should use a comma to separate several sorting rules<br>example:<br>`["backlinks,desc","rank,asc"]` |
| `offset` | integer | *offset in the array of returned results*<br>optional field<br>default value: `0`<br>if you specify the `10` value, the first ten backlinks in the results array will be omitted and the data will be provided for the successive backlinks |
| `limit` | integer | *the maximum number of returned results*<br>optional field<br>default value: `100`<br>maximum value: `1000` |
| `internal_list_limit` | integer | *maximum number of elements within internal arrays*<br>optional field<br>you can use this field to limit the number of elements within the following arrays:<br>`referring_links_tld`<br>`referring_links_types`<br>`referring_links_attributes`<br>`referring_links_platform_types`<br>`referring_links_semantic_locations`<br>default value: `10`<br>maximum value: `1000` |
| `backlinks_status_type` | string | *set what backlinks to return and count*<br>optional field<br>you can use this field to choose what backlinks will be returned and used for aggregated metrics for your `targets`;<br>possible values:<br>`all` – all backlinks will be returned and counted;<br>`live` – backlinks found during the last check will be returned and counted;<br>`lost` – lost backlinks will be returned and counted;<br>default value: `live` |
| `backlinks_filters` | array | *filter the backlinks of your `target`*<br>optional field<br>you can use this field to filter the initial backlinks that will be included in the dataset for aggregated metrics for your `target`<br>you can filter the backlinks by all fields available in the response of [this endpoint](https://docs.dataforseo.com/v3/backlinks/backlinks/live)<br>using this parameter, you can include only dofollow backlinks in the response and create a flexible backlinks dataset to calculate the metrics for<br>example:<br>`"backlinks_filters": [["dofollow", "=", true]]`<br> |
| `include_subdomains` | boolean | *indicates if the subdomains of the `target` will be included in the search*<br>optional field<br>if set to `false`, the subdomains will be ignored<br>default value: `true` |
| `include_indirect_links` | boolean | *indicates if indirect links to the `targets` will be included in the results*<br>optional field<br>if set to `true`, the results will include data on indirect links pointing to a page that either redirects to a target, or points to a canonical page<br>if set to `false`, indirect links will be ignored<br>default value: `true` |
| `exclude_internal_backlinks` | boolean | *indicates whether the backlinks from subdomains of the `target` are excluded*<br>optional field<br>if set to `false`, the backlinks from subdomains of the `target` will be omitted and you won’t receive the same domain in the response;<br>default value: `true` |
| `intersection_mode` | string | *indicates whether to intersect backlinks*<br>optional field<br>use this field to intersect or merge results for the specified domains<br>possible values: `all`, `partial`<br>`all` – results are based on all backlinks;<br>`partial` – results are based on the intersecting backlinks only;<br>default value: `all`<br> |
| `rank_scale` | string | *defines the scale used for calculating and displaying the `rank`, `domain_from_rank`, and `page_from_rank` values*<br>optional field<br>you can use this parameter to choose whether rank values are presented on a 0–100 or 0–1000 scale<br>possible values:<br>`one_hundred` — rank values are displayed on a 0–100 scale<br>`one_thousand` — rank values are displayed on a 0–1000 scale<br>default value: `one_thousand`<br>learn more about how this parameter works and how ranking metrics are calculated in [this Help Center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api#rank_scale) |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `targets` | object | *target domains, subdomains or webpages in a POST array* |
| `total_count` | integer | *total amount of results relevant to your request* |
| `items_count` | integer | *the number of results returned in the `items` array* |
| `**items**` | array | *contains domain that link to all `targets` from the POST array*<br> |
| `**domain_intersection**` | object | *contains data on domains that link to the corresponding targets specified in the POST array*<br>data is provided in separate objects corresponding to domains, subdomains or pages specified in the `targets` object |
| `**1**` | object | *contains data on a domain that links to the corresponding target from the POST array*<br>field name varies in the range from 1 to 20 according to the number of domains, subdomains, or pages in the `targets` object |
| `type` | string | * type of element = **‘backlinks_domain_intersection’*** |
| `target` | string | *domain that links to the corresponding target from the POST array* |
| `rank` | integer | *rank referred to the `target` from the POST array*<br>indicates the rank that the referring domain (`target` above) refers to your target from the POST array;<br>`rank` is calculated based on the method for node ranking in a linked database – a principle used in the original Google PageRank algorithm<br>learn more about the metric and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |
| `backlinks` | integer | *indicates the number of backlinks* |
| `first_seen` | string | *date and time when our crawler found the backlink from this `target` for the first time*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `lost_date` | integer | *date and time when the last backlink from this `target` was lost*<br>indicates the date and time when our crawler visited the page and it responded with 4xx or 5xx status code or the last backlink was removed<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `backlinks_spam_score` | integer | *average spam score of the backlinks pointing to the `target`*<br>learn more about how the metric is calculated on [this help center page](https://dataforseo.com/help-center/what-is-spam-score-and-how-is-it-calculated) |
| `broken_backlinks` | integer | *number of broken backlinks* |
| `broken_pages` | integer | *number of broken pages* |
| `referring_domains` | integer | *number of referring domains* |
| `referring_domains_nofollow` | integer | *number of domains pointing at least one nofollow link to the corresponding target*<br> |
| `referring_main_domains` | integer | *number of referring main domains* |
| `referring_main_domains_nofollow` | integer | *number of main domains pointing at least one nofollow link to the `target`* |
| `referring_ips` | integer | *number of referring IP addresses* |
| `referring_subnets` | integer | *number of referring subnetworks* |
| `referring_pages` | integer | *indicates the number of pages pointing to the `target`* |
| `referring_links_tld` | object | *top level domains of the referring links*<br>contains top-level domains and referring link count per each |
| `referring_links_types` | object | *types of the referring links*<br>indicates the types of referring links and link count per each type<br>possible values:<br>`anchor`, `image`, `link`, `meta`, `canonical`, `alternate`, `redirect` |
| `referring_links_attributes` | object | *link attributes of the referring links*<br>indicates link attributes of the referring links and the link count per each attribute |
| `referring_links_platform_types` | object | *types of referring platforms*<br>indicates referring platform types and link count per each platform<br>possible values: `cms`, `blogs`, `ecommerce`, `message-boards`, `wikis`, `news`, `organization` |
| `referring_links_semantic_locations` | object | *semantic locations of the referring links*<br>indicates semantic elements in HTML where the referring links are located and the link count per each semantic location<br>you can get the full list of semantic elements [here](https://www.w3schools.com/html/html5_semantic_elements.asp) |
| `referring_links_countries` | object | *ISO country codes of the referring links*<br>indicates ISO country codes of the domains where the referring links are located and the link count per each country<br> |
| `referring_pages_nofollow` | integer | *number of referring pages pointing at least one nofollow link to the `target`* |
| `**summary**` | object | *contains the domain intersections summary*<br> |
| `**intersections_count**` | integer | *total number of intersections*<br> |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Page Intersection
*Source: [https://docs.dataforseo.com/v3/backlinks/page_intersection/live/](https://docs.dataforseo.com/v3/backlinks/page_intersection/live/)*
#### Page Intersection

This endpoint will provide you with the list of referring pages pointing to the specified targets. It is especially useful for finding the backlinks that point to your competitors but don’t point to your website.

POSThttps://api.dataforseo.com/v3/backlinks/page_intersection/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/backlinks/backlinks) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute.

You can specify the number of results you want to retrieve, filter and sort them.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `targets` | object | *domains, subdomains or webpages to get links for*<br>**required field**<br>you can set up to 20 domains, subdomains or webpages<br>a domain or a subdomain should be specified without `https://` and `www.`<br>a page should be specified with absolute URL (including `http://` or `https://`)<br>example:<br>`"targets": {<br>"1": "http://planet.postgresql.org/",<br>"2": "http://gborg.postgresql.org/"<br>}` |
| `exclude_targets` | array | *domains, subdomains or webpages you want to exclude*<br>optional field<br>you can set up to 10 domains, subdomains or webpages<br>if you use this array, results will contain the referring pages that link to `targets` but don’t link to `exclude_targets`<br>example:<br>`"exclude_targets": [<br>"bbc.com",<br>"https://www.apple.com/iphone/*",<br>"https://dataforseo.com/apis/*"]`<br> |
| `backlinks_status_type` | string | *set what backlinks to return and count*<br>optional field<br>you can use this field to choose what backlinks will be returned and used for aggregated metrics for your `targets`;<br>possible values:<br>`all` – all backlinks will be returned and counted;<br>`live` – backlinks found during the last check will be returned and counted;<br>`lost` – lost backlinks will be returned and counted;<br>default value: `live` |
| `filters` | array | *array of results filtering parameters*<br>optional field<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`regex`, `not_regex`, `=`, `<>`, `in`, `not_in`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>example:<br>`["1.rank",">","80"]`<br>`[["2.page_from_rank",">","55"],<br>"and",<br>["1.original","=","true"]]`<br>`[["1.first_seen",">","2017-10-23 11:31:45 +00:00"],<br>"and",<br>[["1.acnhor","like","%seo%"],"or",["1.text_pre","not_like","%seo%"]]]`<br>The full list of possible filters is available [here.](https://docs.dataforseo.com/v3/backlinks/filters/?bash) |
| `order_by` | array | *results sorting rules*<br>optional field<br>you can use the same values as in the `filters` array to sort the results<br>possible sorting types:<br>`asc` – results will be sorted in the ascending order<br>`desc` – results will be sorted in the descending order<br>you should use a comma to set up a sorting type<br>example:<br>`["rank,desc"]`<br>**note that you can set no more than three sorting rules in a single request**<br>you should use a comma to separate several sorting rules<br>example:<br>`["domain_from_rank,desc","page_from_rank,asc"]` |
| `offset` | integer | *offset in the results array of the returned backlinks*<br>optional field<br>default value: `0`<br>if you specify the `10` value, the first ten backlinks in the results array will be omitted and the data will be provided for the successive backlinks |
| `limit` | integer | *the maximum number of returned backlinks*<br>optional field<br>default value: `100`<br>maximum value: `1000` |
| `internal_list_limit` | integer | *maximum number of elements within internal arrays*<br>optional field<br>you can use this field to limit the number of elements within the following arrays:<br>`attributes`<br>`domain_from_platform_type`<br>default value: `10`<br>maximum value: `1000` |
| `include_subdomains` | boolean | *indicates if the subdomains of the `targets` will be included in the search*<br>optional field<br>if set to `false`, the subdomains will be ignored<br>default value: `true` |
| `include_indirect_links` | boolean | *indicates if indirect links to the `targets` will be included in the results*<br>optional field<br>if set to `true`, the results will include data on indirect links pointing to a page that either redirects to a target, or points to a canonical page<br>if set to `false`, indirect links will be ignored<br>default value: `true` |
| `exclude_internal_backlinks` | boolean | *indicates if internal backlinks from subdomains to the `target` will be excluded from the results*<br>optional field<br>if set to `true`, the results will not include data on internal backlinks from subdomains of the same domain as `target`<br>if set to `false`, internal links will be included in the result<br>default value: `true` |
| `intersection_mode` | string | *indicates whether to intersect backlinks*<br>optional field<br>use this field to intersect or merge results for the specified URLs<br>possible values: `all`, `partial`<br>`all` – results are based on all backlinks;<br>`partial` – results are based on the intersecting backlinks only;<br>default value: `all`<br> |
| `rank_scale` | string | *defines the scale used for calculating and displaying the `rank`, `domain_from_rank`, and `page_from_rank` values*<br>optional field<br>you can use this parameter to choose whether rank values are presented on a 0–100 or 0–1000 scale<br>possible values:<br>`one_hundred` — rank values are displayed on a 0–100 scale<br>`one_thousand` — rank values are displayed on a 0–1000 scale<br>default value: `one_thousand`<br>learn more about how this parameter works and how ranking metrics are calculated in [this Help Center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api#rank_scale) |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `targets` | object | *`targets` from a POST array* |
| `total_count` | integer | *total amount of results relevant the request* |
| `items_count` | integer | *the number of results returned in the `items` array* |
| `**items**` | array | *contains relevant backlinks and referring domains data* |
| `**page_intersection**` | object | *contains data on pages that link to the corresponding targets specified in the POST array*<br>data is provided in separate objects corresponding to pages specified in the `targets` object |
| `**1**` | array | *contains data on a referring page that links to the corresponding target from the POST array*<br>field name varies in the range from 1 to 20 according to the number of domains, subdomains or pages in the `targets` object |
| `type` | string | * type of element = **‘backlinks_page_intersection’*** |
| `domain_from` | string | *domain referring to the target domain or webpage* |
| `url_from` | string | *URL of the page where the backlink is found* |
| `url_from_https` | boolean | *indicates whether the referring URL is secured with HTTPS*<br>if `true`, the referring URL is secured with HTTPS |
| `domain_to` | string | *domain the backlink is pointing to* |
| `url_to` | string | *URL the backlink is pointing to* |
| `url_to_https` | boolean | *indicates if the URL the backlink is pointing to is secured with HTTPS*<br>if `true`, the URL is secured with HTTPS |
| `tld_from` | string | *top-level domain of the referring URL* |
| `is_new` | boolean | *indicates whether the backlink is new*<br>if `true`, the backlink was found on the page last time our crawler visited it |
| `is_lost` | boolean | *indicates whether the backlink was removed*<br>if `true`, the backlink or the entire page was removed |
| `backlink_spam_score` | integer | *spam score of the backlink*<br>learn more about how the metric is calculated on [this help center page](https://dataforseo.com/help-center/what-is-spam-score-and-how-is-it-calculated) |
| `rank` | integer | *backlink rank*<br>`rank` is calculated based on the method for node ranking in a linked database – a principle used in the original Google PageRank algorithm<br>learn more about the metric and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |
| `page_from_rank` | integer | *page rank of the referring page*<br>`page_from_rank` is calculated based on the method for node ranking in a linked database – a principle used in the original Google PageRank algorithm<br>learn more about the metric and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |
| `domain_from_rank` | integer | *domain rank of the referring domain*<br>indicates the rank of the domain at the time our crawler last saw the backlink;<br>`domain_from_rank` is calculated based on the method for node ranking in a linked database – a principle used in the original Google PageRank algorithm<br>learn more about the metric and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |
| `domain_from_platform_type` | array | *platform types of the referring domain*<br>possible values: `cms`, `blogs`, `ecommerce`, `message-boards`, `wikis`, `news`, `organization` |
| `domain_from_is_ip` | boolean | *indicates if the domain is IP*<br>if `true`, the domain functions as an IP address and does not have a domain name |
| `domain_from_ip` | string | *IP address of the referring domain* |
| `domain_from_country` | string | *ISO country code of the referring domain* |
| `page_from_external_links` | integer | *number of external links found on the referring page* |
| `page_from_internal_links` | integer | *number of internal links found on the referring page* |
| `page_from_size` | integer | *size of the referring page, in bytes*<br>example:<br>`63357` |
| `page_from_encoding` | string | *character encoding of the referring page*<br>example:<br>`utf-8` |
| `page_from_language` | string | *language of the referring page*<br>in ISO 639-1 format<br>example:<br>`en` |
| `page_from_title` | string | *title of the referring page* |
| `page_from_status_code` | integer | *HTTP status code returned by the referring page*<br>example:<br>`200` |
| `first_seen` | string | *date and time when our crawler found the backlink for the first time*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `prev_seen` | string | *previous to the most recent date when our crawler visited the backlink*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `last_seen` | string | *most recent date when our crawler visited the backlink*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `item_type` | string | *link type*<br>possible values:<br>`anchor`, `image`, `link`, `meta`, `canonical`, `alternate`, `redirect` |
| `attributes` | array | *link attributes of the referring links*<br>example:<br>`nofollow` |
| `dofollow` | boolean | *indicates whether the backlink is dofollow*<br>if `false`, the backlink is nofollow |
| `original` | boolean | *indicates whether the backlink was present on the referring page when our crawler first visited it* |
| `alt` | string | *alternative text of the image*<br>this field will be `null` if backlink `type` is not image<br> |
| `anchor` | string | *anchor text of the backlink* |
| `text_pre` | string | *text snippet before the anchor text* |
| `text_post` | string | *snippet after the anchor text* |
| `semantic_location` | string | *indicates semantic element in HTML where the backlink is found*<br>you can get the full list of semantic elements [here](https://www.w3schools.com/html/html5_semantic_elements.asp)<br>examples:<br>`article`, `section`, `summary` |
| `links_count` | integer | *number of identical backlinks found on the referring page* |
| `group_count` | integer | *indicates total number of backlinks from this domain*<br>for example, if `mode` is set to `one_per_domain`, this field will indicate the total number of backlinks coming from this domain |
| `is_broken` | boolean | *indicates whether the backlink is broken*<br>if `true`, the backlink is pointing to a page responding with a 4xx or 5xx status code |
| `url_to_status_code` | integer | *status code of the referenced page*<br>if the value is `null`, our crawler hasn’t yet visited the webpage the link is pointing to<br>example:<br>`200` |
| `url_to_spam_score` | integer | *spam score of the referenced page*<br>if the value is `null`, our crawler hasn’t yet visited the webpage the link is pointing to<br>learn more about how the metric is calculated on [this help center page](https://dataforseo.com/help-center/what-is-spam-score-and-how-is-it-calculated) |
| `url_to_redirect_target` | string | *target url of the redirect*<br>target page the redirect is pointing to |
| `is_indirect_link` | boolean | *indicates whether the backlink is an indirect link*<br>if `true`, the backlink is an indirect link pointing to a page that either redirects to `url_to`, or points to a canonical page |
| `indirect_link_path` | array | *indirect link path*<br>indicates a URL or a sequence of URLs that lead to `url_to` |
| `type` | string | *indirect link type*<br>possible values: `redirect`, `canonical` |
| `status_code` | integer | *HTTP status code of the URL* |
| `url` | string | *indirect link URL* |
| `**summary**` | object | *contains the page intersections summary*<br> |
| `**intersections_count**` | integer | *total number of intersections*<br> |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Domain Pages
*Source: [https://docs.dataforseo.com/v3/backlinks/domain_pages/live/](https://docs.dataforseo.com/v3/backlinks/domain_pages/live/)*
#### Domain Pages

This endpoint will provide you with a detailed overview of domain pages with backlink data for each page.

POSThttps://api.dataforseo.com/v3/backlinks/domain_pages/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/backlinks/backlinks) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `target` | string | *domain or subdomain*<br>**required field**<br>a domain or a subdomain should be specified without `https://` and `www.`<br>example:<br>`forbes.com`<br> |
| `limit` | integer | *the maximum number of returned pages*<br>optional field<br>default value: `100`<br>maximum value: `1000` |
| `offset` | integer | *offset in the results array of returned pages*<br>optional field<br>default value: `0`<br>if you specify the `10` value, the first ten pages in the results array will be omitted and the data will be provided for the successive pages |
| `internal_list_limit` | integer | *maximum number of elements within internal arrays*<br>optional field<br>you can use this field to limit the number of elements within the following arrays:<br>`referring_links_tld`<br>`referring_links_types`<br>`referring_links_attributes`<br>`referring_links_platform_types`<br>`referring_links_semantic_locations`<br>default value: `10`<br>maximum value: `1000` |
| `backlinks_status_type` | string | *set what backlinks to return and count*<br>optional field<br>you can use this field to choose what backlinks will be returned and used for aggregated metrics;<br>possible values:<br>`all` – all backlinks will be returned and counted;<br>`live` – backlinks found during the last check will be returned and counted;<br>`lost` – lost backlinks will be returned and counted;<br>default value: `live` |
| `filters` | array | *array of results filtering parameters*<br>optional field<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`regex`, `not_regex`, `=`, `<>`, `in`, `not_in`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>example:<br>`["meta.internal_links_count",">","1"]`<br>`[["meta.external_links_count",">","2"],<br>"and",<br>["backlinks",">","10"]]`<br>`[["first_visited",">","2017-10-23 11:31:45 +00:00"],<br>"and",<br>[["title","like","%seo%"],"or",["referring_domains",">","10"]]]`<br>The full list of possible filters is available [here.](https://docs.dataforseo.com/v3/backlinks/filters/?bash) |
| `order_by` | array | *results sorting rules*<br>optional field<br>you can use the same values as in the `filters` array to sort the results<br>possible sorting types:<br>`asc` – results will be sorted in the ascending order<br>`desc` – results will be sorted in the descending order<br>you should use a comma to set up a sorting type<br>example:<br>`["page_summary.backlinks,desc"]`<br>**note that you can set no more than three sorting rules in a single request**<br>you should use a comma to separate several sorting rules<br>example:<br>`["page_summary.backlinks,desc","page_summary.rank,asc"]` |
| `backlinks_filters` | array | *filter the backlinks of your `target`*<br>optional field<br>you can use this field to filter the initial backlinks that will be included in the dataset for aggregated metrics for your `target`<br>you can filter the backlinks by all fields available in the response of [this endpoint](https://docs.dataforseo.com/v3/backlinks/backlinks/live)<br>using this parameter, you can include only dofollow backlinks in the response and create a flexible backlinks dataset to calculate the metrics for<br>example:<br>`"backlinks_filters": ["dofollow", "=", true]`<br> |
| `include_subdomains` | boolean | *indicates if the subdomains of the `target` will be included in the search*<br>optional field<br>if set to `false`, the subdomains will be ignored<br>default value: `true` |
| `exclude_internal_backlinks` | boolean | *indicates if internal backlinks from subdomains to the `target` will be excluded from the results*<br>optional field<br>if set to `true`, the results will not include data on internal backlinks from subdomains of the same domain as `target`<br>if set to `false`, internal links will be included in the results<br>default value: `true` |
| `rank_scale` | string | *defines the scale used for calculating and displaying the `rank`, `domain_from_rank`, and `page_from_rank` values*<br>optional field<br>you can use this parameter to choose whether rank values are presented on a 0–100 or 0–1000 scale<br>possible values:<br>`one_hundred` — rank values are displayed on a 0–100 scale<br>`one_thousand` — rank values are displayed on a 0–1000 scale<br>default value: `one_thousand`<br>learn more about how this parameter works and how ranking metrics are calculated in [this Help Center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api#rank_scale) |
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
| `target` | string | *`target` in a POST array*<br> |
| `total_count` | integer | *total number of relevant items in the database*<br> |
| `items_count` | integer | *number of items in the `items` array*<br> |
| **`items`** | array | *items array*<br> |
| `type` | string | * type of element = **‘backlinks_domain_page’*** |
| `main_domain` | string | *main website domain*<br>main website domain does not include subdomains<br> |
| `domain` | string | *domain*<br>domain where the page was found |
| `tld` | string | *top-level domain*<br>top-level domain in the [DNS root zone](https://www.iana.org/domains/root/db) |
| `page` | string | *page URL*<br>relevant page URL |
| `ip` | string | *Internet Protocol address*<br> |
| `first_visited` | string | *date and time of the first page visit*<br>date and time when our crawler visited this page for the first time<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2017-01-24 13:20:59 +00:00` |
| `prev_visited` | string | *previous to the most recent date when our crawler visited the page*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2017-01-24 13:20:59 +00:00` |
| `fetch_time` | string | *most recent date and time when our crawler visited the page*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2017-01-24 13:20:59 +00:00` |
| `status code` | integer | *HTTP status code of the page*<br> |
| `location` | string | *location header*<br>indicates the URL to redirect a page to if exists<br> |
| `size` | integer | *indicates the page size, in bytes*<br> |
| `encoded_size` | integer | *page size after encoding*<br>indicates the size of the encoded page, in bytes |
| `content_encoding` | string | *type of encoding* |
| `media_type` | string | *types of media used to display a page* |
| `server` | string | *server version* |
| `meta` | object | *page meta data*<br> |
| `title` | string | *page title*<br> |
| `canonical` | string | *canonical page*<br> |
| `internal_links_count` | integer | *number of internal links on the page* |
| `external_links_count` | integer | *number of external links on the page* |
| `images_count` | integer | *number of images on the page* |
| `words_count` | integer | *number of words on the page* |
| `page_spam_score` | integer | *spam score of the page*<br>learn more about how the metric is calculated on [this help center page](https://dataforseo.com/help-center/what-is-spam-score-and-how-is-it-calculated) |
| `social_media_tags` | object | *array of social media tags found on the page*<br>contains social media tags and their content<br>supported tags include but are not limited to [Open Graph](https://ogp.me/) and [Twitter card](https://developer.twitter.com/en/docs/twitter-for-websites/cards/guides/getting-started) |
| `h1` | array | *h1 tag*<br>content of `h1` tags<br> |
| `h2` | array | *h2 tag*<br>content of `h2` tags<br> |
| `h3` | array | *h3 tag*<br>content of `h3` tags<br> |
| `images_alt` | array | *content of `alt` tags*<br> |
| `powered_by` | array | *CMS details*<br> |
| `language` | string | *page content language*<br>example:<br>`en`<br> |
| `charset` | string | *character encoding*<br>examples:<br>`utf-8`<br> |
| `platform_type` | array | *type of a platform*<br> |
| `technologies` | object | *website technologies*<br> |
| `cms` | string | *content management system*<br> |
| `blogs` | string | *blog management system*<br> |
| `cdn` | string | *content delivery network*<br> |
| `page_summary` | object | *contains backlink data for this page* |
| `first_seen` | string | *date and time when our crawler found the backlink for the first time*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `lost_date` | string | *date and time when the last backlink for this page was lost*<br>indicates the date and time when our crawler visited the page and it responded with 4xx or 5xx status code or the last backlink was removed<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2017-01-24 13:20:59 +00:00` |
| `rank` | integer | *page rank*<br>rank of the `page`<br>`rank` is calculated based on the method for node ranking in a linked database – a principle used in the original Google PageRank algorithm<br>learn more about the metric and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |
| `backlinks` | integer | *indicates the number of backlinks*<br> |
| `backlinks_spam_score` | integer | *average spam score of the backlinks pointing to the page*<br>learn more about how the metric is calculated on [this help center page](https://dataforseo.com/help-center/what-is-spam-score-and-how-is-it-calculated) |
| `broken_backlinks` | integer | *number of broken backlinks*<br>number of broken backlinks pointing to the `page`<br> |
| `broken_pages` | integer | *number of broken pages*<br>number of pages that respond with 4xx or 5xx status codes where backlinks are pointing to<br> |
| `referring_domains` | integer | *indicates the number of referring domains*<br> |
| `referring_domains_nofollow` | integer | *number of domains pointing at least one nofollow link to the `page`*<br> |
| `referring_main_domains` | integer | *indicates the number of referring main domains*<br> |
| `referring_main_domains_nofollow` | integer | *number of main domains pointing at least one nofollow link to the `page`* |
| `referring ips` | integer | *number of referring IP addresses*<br>number of IP addresses pointing to this page<br> |
| `referring subnets` | integer | *number of referring subnetworks*<br> |
| `referring_pages` | integer | *indicates the number of pages pointing to the `page`*<br> |
| `referring_links_tld` | object | *top-level domains of the referring links*<br>contains top level domains and referring link count per each<br> |
| `referring_links_types` | object | *types of referring links*<br>indicates the types of the referring links and link count per each type<br>possible values:<br>`anchor`, `image`, `link`, `meta`, `canonical`, `alternate`, `redirect`<br> |
| `referring_links_attributes` | object | *link attributes of the referring links*<br>indicates link attributes of the referring links and link count per each attribute<br> |
| `referring_links_platform_types` | object | *types of referring platforms*<br>indicates referring platform types and and link count per each platform<br>possible values: `cms`, `blogs`, `ecommerce`, `message-boards`, `wikis`, `news`, `organization` |
| `referring_links_semantic_locations` | object | *semantic locations of the referring links*<br>indicates semantic elements in HTML where the referring links are located and link count per each semantic location<br>you can get the full list of semantic elements [here](https://www.w3schools.com/html/html5_semantic_elements.asp)<br>examples:<br>`article`, `section`, `summary` |
| `referring_links_countries` | object | *ISO country codes of the referring links*<br>indicates ISO country codes of the domains where the referring links are located and the link count per each country<br> |
| `referring_pages_nofollow` | integer | *number of referring pages pointing at least one nofollow link to the `page`* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Domain Pages Summary
*Source: [https://docs.dataforseo.com/v3/backlinks/domain_pages_summary/live/](https://docs.dataforseo.com/v3/backlinks/domain_pages_summary/live/)*
#### Domain Pages Summary

This endpoint will provide you with detailed summary data on all backlinks and related metrics for each page of the target domain or subdomain you specify. If you indicate a single page as a target, you will get comprehensive summary data on all backlinks for that page.

POSThttps://api.dataforseo.com/v3/backlinks/domain_pages_summary/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/backlinks/backlinks) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `target` | string | *domain, subdomain or webpage to get summary data for*<br>**required field**<br>a domain or a subdomain should be specified without `https://` and `www.`<br>a page should be specified with absolute URL (including `http://` or `https://`) |
| `limit` | integer | *the maximum number of returned anchors*<br>optional field<br>default value: `100`<br>maximum value: `1000` |
| `offset` | integer | *offset in the results array of returned anchors*<br>optional field<br>default value: `0`<br>if you specify the `10` value, the first ten anchors in the results array will be omitted and the data will be provided for the successive anchors |
| `internal_list_limit` | integer | *maximum number of elements within internal arrays*<br>optional field<br>you can use this field to limit the number of elements within the following arrays:<br>`referring_links_tld`<br>`referring_links_types`<br>`referring_links_attributes`<br>`referring_links_platform_types`<br>`referring_links_semantic_locations`<br>default value: `10`<br>maximum value: `1000` |
| `backlinks_status_type` | string | *set what backlinks to return and count*<br>optional field<br>you can use this field to choose what backlinks will be returned and used for aggregated metrics for your `target`;<br>possible values:<br>`all` – all backlinks will be returned and counted;<br>`live` – backlinks found during the last check will be returned and counted;<br>`lost` – lost backlinks will be returned and counted;<br>default value: `live` |
| `filters` | array | *array of results filtering parameters*<br>optional field<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`regex`, `not_regex`, `=`, `<>`, `in`, `not_in`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>example:<br>`["referring_links_types.anchors",">","1"]`<br>`[["broken_pages",">","2"],<br>"and",<br>["backlinks",">","10"]]`<br>`[["first_seen",">","2017-10-23 11:31:45 +00:00"],<br>"and",<br>[["anchor","like","%seo%"],"or",["referring_domains",">","10"]]]`<br>The full list of possible filters is available [here.](https://docs.dataforseo.com/v3/backlinks/filters/?bash) |
| `order_by` | array | *results sorting rules*<br>optional field<br>you can use the same values as in the `filters` array to sort the results<br>possible sorting types:<br>`asc` – results will be sorted in the ascending order<br>`desc` – results will be sorted in the descending order<br>you should use a comma to set up a sorting type<br>example:<br>`["backlinks,desc"]`<br>**note that you can set no more than three sorting rules in a single request**<br>you should use a comma to separate several sorting rules<br>example:<br>`["backlinks,desc","rank,asc"]` |
| `backlinks_filters` | array | *filter the backlinks of your `target`*<br>optional field<br>you can use this field to filter the initial backlinks that will be included in the dataset for aggregated metrics for your `target`<br>you can filter the backlinks by all fields available in the response of [this endpoint](https://docs.dataforseo.com/v3/backlinks/backlinks/live/)<br>using this parameter, you can include only dofollow backlinks in the response and create a flexible backlinks dataset to calculate the metrics for<br>example:<br>`"backlinks_filters": [["dofollow", "=", true]]`<br> |
| `include_subdomains` | boolean | *indicates if the subdomains of the `target` domain will be included in the search*<br>optional field<br>if set to `false`, the subdomains will be ignored<br>default value: `true` |
| `include_indirect_links` | boolean | *indicates if indirect links to the `target` will be included in the results*<br>optional field<br>if set to `true`, the results will include data on indirect links pointing to a page that either redirects to the target, or points to a canonical page<br>if set to `false`, indirect links will be ignored<br>default value: `true` |
| `exclude_internal_backlinks` | boolean | *indicates whether the backlinks from subdomains of the `target` are excluded*<br>optional field<br>if set to `false`, backlinks from the subdomains of the `target` domain will be ommited and you won’t receive the same domain in the response;<br>default value: `true` |
| `rank_scale` | string | *defines the scale used for calculating and displaying the `rank`, `domain_from_rank`, and `page_from_rank` values*<br>optional field<br>you can use this parameter to choose whether rank values are presented on a 0–100 or 0–1000 scale<br>possible values:<br>`one_hundred` — rank values are displayed on a 0–100 scale<br>`one_thousand` — rank values are displayed on a 0–1000 scale<br>default value: `one_thousand`<br>learn more about how this parameter works and how ranking metrics are calculated in [this Help Center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api#rank_scale) |
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
| `target` | string | *target in the post array*<br> |
| `total_count` | integer | *total number of relevant items in the database*<br> |
| `items_count` | integer | *number of items in the results array*<br> |
| **`items`** | array | *items array*<br> |
| `type` | string | * type of element = **‘backlinks_page_summary’*** |
| `url` | string | *page URL* |
| `rank` | integer | *page rank*<br>rank of the `page`<br>`rank` is calculated based on the method for node ranking in a linked database – a principle used in the original Google PageRank algorithm<br>learn more about the metric and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |
| `backlinks` | integer | *number of backlinks*<br> |
| `first_seen` | string | *date and time when our crawler found a backlink to this page for the first time*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `lost_date` | string | *date and time when the last backlink to this page was lost*<br>indicates the date and time when our crawler visited the page and it responded with 4xx or 5xx status code or the last backlink was removed<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2017-01-24 13:20:59 +00:00` |
| `backlinks_spam_score` | integer | *average spam score of the backlinks pointing to the page*<br>learn more about how the metric is calculated on [this help center page](https://dataforseo.com/help-center/what-is-spam-score-and-how-is-it-calculated) |
| `broken_backlinks` | integer | *number of broken backlinks*<br>number of broken backlinks pointing to the page |
| `broken_pages` | integer | *number of broken pages*<br>number of pages that respond with 4xx or 5xx status codes where backlinks are pointing to |
| `referring_domains` | integer | *indicates the number domains referring to the page*<br> |
| `referring_domains_nofollow` | integer | *number of domains pointing at least one nofollow link to the `page`*<br> |
| `referring_main_domains` | integer | *indicates the number of referring main domains*<br> |
| `referring_main_domains_nofollow` | integer | *number of main domains pointing at least one nofollow link to the `page`* |
| `referring_ips` | integer | *number of referring IP addresses*<br>number of IP addresses pointing to this page<br> |
| `referring_subnets` | integer | *number of referring subnetworks*<br> |
| `referring_pages` | integer | *indicates the number of pages pointing to the relevant `url`*<br> |
| `referring_links_tld` | object | *top-level domains of the referring links*<br>contains top level domains and referring link count per each<br> |
| `referring_links_types` | object | *types of referring links*<br>indicates the types of the referring links and link count per each type<br>possible values:<br>`anchor`, `image`, `link`, `meta`, `canonical`, `alternate`, `redirect`<br> |
| `referring_links_attributes` | object | *link attributes of the referring links*<br>indicates link attributes of the referring links and link count per each attribute<br> |
| `referring_links_platform_types` | object | *types of referring platforms*<br>indicates referring platform types and and link count per each platform<br>possible values: `cms`, `blogs`, `ecommerce`, `message-boards`, `wikis`, `news`, `organization` |
| `referring_links_semantic_locations` | object | *semantic locations of the referring links*<br>indicates semantic elements in HTML where the referring links are located and link count per each semantic location<br>you can get the full list of semantic elements [here](https://www.w3schools.com/html/html5_semantic_elements.asp)<br>examples:<br>`article`, `section`, `footer` |
| `referring_links_countries` | object | *ISO country codes of the referring links*<br>indicates ISO country codes of the domains where the referring links are located and the link count per each country<br> |
| `referring_pages_nofollow` | integer | *number of referring pages pointing at least one nofollow link to the `page`* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Timeseries Summary ‌
*Source: [https://docs.dataforseo.com/v3/backlinks/timeseries_summary/live/](https://docs.dataforseo.com/v3/backlinks/timeseries_summary/live/)*
#### Backlinks Timeseries Summary

This endpoint will provide you with an overview of backlink data for the `target` domain available during a period between the two indicated dates. Backlink metrics will be grouped by the time range that you define: day, week, month, or year.

Data from this endpoint will be especially helpful for building time-series graphs of daily, weekly, monthly, and yearly link-building progress.

Historical data is available from `2019-01-30`.

POSThttps://api.dataforseo.com/v3/backlinks/timeseries_summary/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/backlinks/backlinks) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. The maximum number of requests that can be sent simultaneously is limited to 30.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `target` | string | *domain to get data for*<br>**required field**<br>a domain should be specified without `https://` and `www.`<br>example:<br>`"forbes.com"` |
| `date_from` | string | *starting date of the time range*<br>optional field<br>this field indicates the date which will be used as a threshold for summary data;<br>minimum value: `2019-01-30`<br>maximum value shouldn’t exceed the date specified in the `date_to`<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2021-01-01"` |
| `date_to` | string | *ending date of the time range*<br>optional field<br>if you don’t specify this field, the today’s date will be used by default<br>minimum value shouldn’t preceed the date specified in the `date_from`<br>maximum value: today’s date<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2021-01-15"` |
| `group_range` | string | *time range which will be used to group the results*<br>optional field<br>default value: `month`<br>possible values: `day`, `week`, `month`, `year`<br>**note:** for `day`, we will return items corresponding to all dates between and including `date_from` and `date_to`;<br>for `week`/`month`/`year`, we will return items corresponding to full weeks/months/years, where each item will indicate the last day of the week/month/year<br>for example, if you specify:<br>`"group_range": "month",<br>"date_from": "2022-03-23",<br>"date_to": "2022-05-13"`<br>we will return items falling between 2022-03-01 and 2022-05-31, namely, three items corresponding to the following dates: `2022-03-31`, `2022-04-30`, `2022-05-31`<br>if there is no data for a certain `day`/`week`/`month`/`year`, we will return `0` |
| `include_subdomains` | boolean | *indicates if the subdomains of the `target` will be included in the search*<br>optional field<br>if set to `false`, the subdomains will be ignored<br>default value: `true` |
| `rank_scale` | string | *defines the scale used for calculating and displaying the `rank`, `domain_from_rank`, and `page_from_rank` values*<br>optional field<br>you can use this parameter to choose whether rank values are presented on a 0–100 or 0–1000 scale<br>possible values:<br>`one_hundred` — rank values are displayed on a 0–100 scale<br>`one_thousand` — rank values are displayed on a 0–1000 scale<br>default value: `one_thousand`<br>learn more about how this parameter works and how ranking metrics are calculated in [this Help Center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api#rank_scale) |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `target` | string | *`target` from a POST array* |
| `date_from` | string | *starting date of the time range*<br>in the UTC format: “yyyy-mm-dd”<br>example:<br>`2019-01-01` |
| `date_to` | string | *ending date of the time range*<br>in the UTC format: `"yyyy-mm-dd"`<br>example:<br>`"2019-01-15"` |
| `group_range` | object | *`group_range` from a POST array* |
| `total_count` | integer | *total amount of results relevant the request* |
| `items_count` | integer | *the number of results returned in the `items` array* |
| `**items**` | array | *contains relevant summary data* |
| `type` | string | * type of element = **‘backlinks_timeseries_summary’*** |
| `date` | string | *date and time when the data for the target was stored*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `rank` | integer | *`target` rank for the given `date`*<br>learn more about the metric and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |
| `backlinks` | integer | *number of backlinks for the given `date`* |
| `backlinks_nofollow` | integer | *number of nofollow backlinks for the given `date`* |
| `referring_pages` | integer | *number of pages pointing to `target` for the given `date`* |
| `referring_domains` | integer | *number of referring domains for the given `date`*<br>referring domains include subdomains that are counted as separate domains for this metric |
| `referring_domains_nofollow` | integer | *number of domains pointing at least one nofollow link to the `target` for the given `date`*<br> |
| `referring_main_domains` | integer | *number of referring main domains for the given `date`*<br> |
| `referring_main_domains_nofollow` | integer | *number of main domains pointing at least one nofollow link to the `target` for the given `date`*<br> |
| `referring_ips` | integer | *number of referring IP addresses for the given `date`*<br>number of IP addresses pointing to this page |
| `referring_subnets` | integer | *number of referring subnetworks for the given `date`* |
| `referring_pages_nofollow` | integer | *number of referring pages pointing at least one nofollow link to the `target` for the given `date`* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### New & Lost Timeseries
*Source: [https://docs.dataforseo.com/v3/backlinks/timeseries_new_lost_summary/live/](https://docs.dataforseo.com/v3/backlinks/timeseries_new_lost_summary/live/)*
#### New & Lost Backlinks Timeseries Summary

This endpoint will provide you with the number of new and lost backlinks and referring domains for the domain specified in the `target` field.

The results will be provided for a period between the two indicated dates, and metrics will be grouped by the time range that you define: day, week, month, or year.

Data from this endpoint will be especially helpful for building time-series graphs of new and lost backlinks and referring domains.

Historical data is available from `2019-01-30`.

POSThttps://api.dataforseo.com/v3/backlinks/timeseries_new_lost_summary/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/backlinks/backlinks) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. The maximum number of requests that can be sent simultaneously is limited to 30.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `target` | string | *domain to get data for*<br>**required field**<br>a domain should be specified without `https://` and `www.`<br>example:<br>`"forbes.com"` |
| `date_from` | string | *starting date of the time range*<br>optional field<br>this field indicates the date which will be used as a threshold for new and lost backlinks and referring domains;<br>the backlinks and referring domains that appeared in our index after the specified date will be considered as new;<br>the backlinks and referring domains that weren’t found after the specified date, but were present before, will be considered as lost;<br>minimum value: `2019-01-30`<br>maximum value shouldn’t exceed the date specified in the `date_to`<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2021-01-01"` |
| `date_to` | string | *ending date of the time range*<br>optional field<br>if you don’t specify this field, the today’s date will be used by default<br>minimum value shouldn’t preceed the date specified in the `date_from`<br>maximum value: today’s date<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2021-01-15"` |
| `group_range` | string | *time range which will be used to group the results*<br>optional field<br>default value: `month`<br>possible values: `day`, `week`, `month`, `year`<br>**note:** for `day`, we will return items corresponding to all dates between and including `date_from` and `date_to`;<br>for `week`/`month`/`year`, we will return items corresponding to full weeks/months/years, where each item will indicate the last day of the week/month/year<br>for example, if you specify:<br>`"group_range": "month",<br>"date_from": "2022-03-23",<br>"date_to": "2022-05-13"`<br>we will return items falling between 2022-03-01 and 2022-05-31, namely, three items corresponding to the following dates: `2022-03-31`, `2022-04-30`, `2022-05-31`<br>if there is no data for a certain `day`/`week`/`month`/`year`, we will return `0` |
| `include_subdomains` | boolean | *indicates if the subdomains of the `target` will be included in the search*<br>optional field<br>if set to `false`, the subdomains will be ignored<br>default value: `true` |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `target` | string | *`target` from a POST array* |
| `date_from` | string | *starting date of the time range*<br>in the UTC format: “yyyy-mm-dd”<br>example:<br>`2019-01-01` |
| `date_to` | string | *ending date of the time range*<br>in the UTC format: `"yyyy-mm-dd"`<br>example:<br>`"2019-01-15"` |
| `group_range` | string | *`group_range` from the POST array* |
| `total_count` | integer | *total amount of results relevant the request* |
| `items_count` | integer | *the number of results returned in the `items` array* |
| `**items**` | array | *contains relevant backlinks and referring domains data* |
| `type` | string | * type of element = **‘backlinks_timeseries_new_lost_summary’*** |
| `date` | string | *date and time when the data for the target was stored*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00`<br> |
| `new_backlinks` | integer | *number of new backlinks*<br>number of new backlinks pointing to the `target`<br> |
| `lost_backlinks` | integer | *number of lost backlinks*<br>number of lost backlinks of the `target`<br> |
| `new_referring_domains` | integer | *number of new referring domains*<br>number of new referring domains pointing to the `target`<br> |
| `lost_referring_domains` | integer | *number of lost referring domains*<br>number of lost referring domains of the `target`<br> |
| `new_referring_main_domains` | integer | *number of new referring main domains*<br>number of new referring main domains pointing to the `target`<br> |
| `lost_referring_main_domains` | integer | *number of lost referring main domains*<br>number of lost referring main domains of the `target`<br> |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Bulk Ranks
*Source: [https://docs.dataforseo.com/v3/backlinks/bulk_ranks/live/](https://docs.dataforseo.com/v3/backlinks/bulk_ranks/live/)*
#### Bulk Ranks

This endpoint will provide you with rank scores of the domains, subdomains, and pages specified in the `targets` array. The score is based on the number of referring domains pointing to the specified domains, subdomains, or pages. The `rank` values represent real-time data for the date of the request and range from 0 (no backlinks detected) to 1,000 (highest rank). A similar scoring system is used in Google’s Page Rank algorithm. You can learn more about rank scores in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api)

POSThttps://api.dataforseo.com/v3/backlinks/bulk_ranks/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/backlinks/backlinks) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. The maximum number of requests that can be sent simultaneously is limited to 30.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `targets` | array | *domains, subdomains or webpages to get `rank` for*<br>**required field**<br>you can set up to 1000 domains, subdomains or webpages<br>the domain or subdomain should be specified without `https://` and `www.`<br>the page should be specified with absolute URL (including `http://` or `https://`)<br>example:<br>`"targets": [<br> "forbes.com",<br> "cnn.com",<br> "bbc.com",<br> "yelp.com",<br> "https://www.apple.com/iphone/",<br> "https://ahrefs.com/blog/",<br> "ibm.com",<br> "https://variety.com/",<br> "https://stackoverflow.com/",<br> "www.trustpilot.com"<br>]` |
| `rank_scale` | string | *defines the scale used for calculating and displaying the `rank`, `domain_from_rank`, and `page_from_rank` values*<br>optional field<br>you can use this parameter to choose whether rank values are presented on a 0–100 or 0–1000 scale<br>possible values:<br>`one_hundred` — rank values are displayed on a 0–100 scale<br>`one_thousand` — rank values are displayed on a 0–1000 scale<br>default value: `one_thousand`<br>learn more about how this parameter works and how ranking metrics are calculated in [this Help Center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api#rank_scale) |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `items_count` | integer | *the number of results returned in the `items` array* |
| `**items**` | array | *contains relevant backlinks and referring domains data* |
| `target` | string | *domain, subdomain or webpage from a POST array*<br> |
| `rank` | integer | *rank of the `target`*<br>values represent real-time data for the date of the request<br>`rank` is calculated based on the method for node ranking in a linked database – a principle used in the original Google PageRank algorithm<br>learn more about the metric and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Bulk Backlinks
*Source: [https://docs.dataforseo.com/v3/backlinks/bulk_backlinks/live/](https://docs.dataforseo.com/v3/backlinks/bulk_backlinks/live/)*
#### Bulk Backlinks

This endpoint will provide you with the number of backlinks pointing to domains, subdomains, and pages specified in the `targets` array. The returned numbers correspond to all **live** backlinks, that is, total number of referring links with all attributes (e.g., nofollow, noreferrer, ugc, sponsored etc) that were found during the latest check.

Note that if you indicate a domain as a target, you will get results for the root domain (domain with all of its subdomains), e.g. `dataforseo.com` and `app.dataforseo.com`

POSThttps://api.dataforseo.com/v3/backlinks/bulk_backlinks/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/backlinks/backlinks) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. The maximum number of requests that can be sent simultaneously is limited to 30.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `targets` | array | *domains, subdomains or webpages to get the number of backlinks for*<br>**required field**<br>you can set up to 1000 domains, subdomains or webpages<br>the domain or subdomain should be specified without `https://` and `www.`<br>the page should be specified with absolute URL (including `http://` or `https://`)<br>example:<br>`"targets": [<br> "forbes.com",<br> "cnn.com",<br> "bbc.com",<br> "yelp.com",<br> "https://www.apple.com/iphone/",<br> "https://ahrefs.com/blog/",<br> "ibm.com",<br> "https://variety.com/",<br> "https://stackoverflow.com/",<br> "www.trustpilot.com"<br>]` |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `items_count` | integer | *the number of results returned in the `items` array* |
| `**items**` | array | *contains relevant backlink data* |
| `target` | string | *domain, subdomain or webpage from a POST array*<br> |
| `backlinks` | integer | *number of backlinks pointing to the `target`*<br> |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Bulk Spam Score
*Source: [https://docs.dataforseo.com/v3/backlinks/bulk_spam_score/live/](https://docs.dataforseo.com/v3/backlinks/bulk_spam_score/live/)*
#### Bulk Spam Score

This endpoint will provide you with spam scores of the domains, subdomains, and pages you specified in the `targets` array. Spam Score is DataForSEO’s proprietary metric that indicates how “spammy” your target is on a scale from 0 to 100. You can learn more about Spam Score, how it is calculated, and signals it takes into account in [this help center article](https://dataforseo.com/help-center/what-is-spam-score-and-how-is-it-calculated)

POSThttps://api.dataforseo.com/v3/backlinks/bulk_spam_score/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/backlinks/backlinks) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. The maximum number of requests that can be sent simultaneously is limited to 30.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `targets` | array | *domains, subdomains or webpages to get `rank` for*<br>**required field**<br>you can set up to 1000 domains, subdomains or webpages<br>the domain or subdomain should be specified without `https://` and `www.`<br>the page should be specified with absolute URL (including `http://` or `https://`)<br>example:<br>`"targets": [<br> "forbes.com",<br> "cnn.com",<br> "bbc.com",<br> "yelp.com",<br> "https://www.apple.com/iphone/",<br> "https://ahrefs.com/blog/",<br> "ibm.com",<br> "https://variety.com/",<br> "https://stackoverflow.com/",<br> "www.trustpilot.com"<br>]` |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `items_count` | integer | *the number of results returned in the `items` array* |
| `**items**` | array | *contains relevant backlinks and referring domains data* |
| `type` | string | *type = **‘backlinks_bulk_spam_score’***<br> |
| `target` | string | *domain, subdomain or webpage from a POST array*<br> |
| `spam_score` | integer | *average spam score the target*<br>[learn more](https://dataforseo.com/help-center/what-is-spam-score-and-how-is-it-calculated) about how the metric is calculated |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Bulk Referring Domains
*Source: [https://docs.dataforseo.com/v3/backlinks/bulk_referring_domains/live/](https://docs.dataforseo.com/v3/backlinks/bulk_referring_domains/live/)*
#### Bulk Referring Domains

This endpoint will provide you with the number of referring domains pointing to domains, subdomains, and pages specified in the `targets` array. The returned numbers are based on all **live** referring domains, that is, total number of domains pointing to the target with any type of backlinks (e.g., nofollow, noreferrer, ugc, sponsored etc) that were found during the latest check.

Note that if you indicate a domain as a target, you will get result for the root domain (domain with all of its subdomains), e.g. `dataforseo.com` and `app.dataforseo.com`

POSThttps://api.dataforseo.com/v3/backlinks/bulk_referring_domains/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/backlinks/backlinks) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. The maximum number of requests that can be sent simultaneously is limited to 30.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `targets` | array | *domains, subdomains or webpages to get the number of referring domains for*<br>**required field**<br>you can set up to 1000 domains, subdomains or webpages<br>the domain or subdomain should be specified without `https://` and `www.`<br>the page should be specified with absolute URL (including `http://` or `https://`)<br>example:<br>`"targets": [<br> "forbes.com",<br> "cnn.com",<br> "bbc.com",<br> "yelp.com",<br> "https://www.apple.com/iphone/",<br> "https://ahrefs.com/blog/",<br> "ibm.com",<br> "https://variety.com/",<br> "https://stackoverflow.com/",<br> "www.trustpilot.com"<br>]` |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `items_count` | integer | *the number of results returned in the `items` array* |
| `**items**` | array | *contains relevant backlinks and referring domains data* |
| `target` | string | *domain, subdomain or webpage from a POST array*<br> |
| `referring_domains` | integer | *number of referring domains pointing to the `target`*<br>note that we calculate main domains (root domains, like `example.com`) and their subdomains (e.g. `blog.example.com`) separately for this metric |
| `referring_domains_nofollow` | integer | *number of domains pointing at least one nofollow link to the `target`*<br> |
| `referring_main_domains` | integer | *number of referring main domains pointing to the `target`*<br>the number of primary (root) domains referring to your target |
| `referring_main_domains_nofollow` | integer | *number of main domains pointing at least one nofollow link to the `target`*<br> |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Bulk New & Lost Backlinks
*Source: [https://docs.dataforseo.com/v3/backlinks/bulk_new_lost_backlinks/live/](https://docs.dataforseo.com/v3/backlinks/bulk_new_lost_backlinks/live/)*
#### Bulk New & Lost Backlinks

This endpoint will provide you with the number of new and lost backlinks for the domains, subdomains, and pages specified in the `targets` array.

Note that if you indicate a domain as a target, you will get result for the root domain (domain with all of its subdomains), e.g. `dataforseo.com` and `app.dataforseo.com`

Historical data is available for the last 365 days.

POSThttps://api.dataforseo.com/v3/backlinks/bulk_new_lost_backlinks/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/backlinks/backlinks) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. The maximum number of requests that can be sent simultaneously is limited to 30.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `targets` | array | *domains, subdomains or webpages to get new & lost backlinks for*<br>**required field**<br>you can set up to 1000 domains, subdomains or webpages<br>the domain or subdomain should be specified without `https://` and `www.`<br>the page should be specified with absolute URL (including `http://` or `https://`)<br>example:<br>`"targets": [<br> "forbes.com",<br> "cnn.com",<br> "bbc.com",<br> "yelp.com",<br> "https://www.apple.com/iphone/",<br> "https://ahrefs.com/blog/",<br> "ibm.com",<br> "https://variety.com/",<br> "https://stackoverflow.com/",<br> "www.trustpilot.com"<br>]` |
| `date_from` | string | *starting date of the time range*<br>optional field<br>this field indicates the date which will be used as a threshold for new and lost backlinks;<br>the backlinks that appeared in our index after the specified date will be considered as new;<br>the backlinks that weren’t found after the specified date, but were present before, will be considered as lost;<br>default value: today’s date -(minus) one month;<br>e.g. if today is `2021-10-13`, default `date_from` will be `2021-09-13`.<br>**minimum value equals today’s date -(minus) one year;**<br>e.g. if today is `2021-10-13`, minimum `date_from` will be `2020-10-13`.<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2021-01-01"` |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `items_count` | integer | *the number of results returned in the `items` array* |
| `**items**` | array | *contains relevant backlinks and referring domains data* |
| `target` | string | *domain, subdomain or webpage from a POST array*<br> |
| `new_backlinks` | integer | *number of new backlinks*<br>number of new backlinks pointing to the `target`<br> |
| `lost_backlinks` | integer | *number of lost backlinks*<br>number of lost backlinks of the `target`<br> |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Bulk New & Lost Referring Domains
*Source: [https://docs.dataforseo.com/v3/backlinks/bulk_new_lost_referring_domains/live/](https://docs.dataforseo.com/v3/backlinks/bulk_new_lost_referring_domains/live/)*
#### Bulk New & Lost Referring Domains

This endpoint will provide you with the number of referring domains pointing to the domains, subdomains and pages specified in the `targets` array.

Note that if you indicate a domain as a target, you will get result for the root domain (domain with all of its subdomains), e.g. `dataforseo.com` and `app.dataforseo.com`

Historical data is available for the last 365 days.

POSThttps://api.dataforseo.com/v3/backlinks/bulk_new_lost_referring_domains/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/backlinks/backlinks) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. The maximum number of requests that can be sent simultaneously is limited to 30.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `targets` | array | *domains, subdomains or webpages to get new & lost referring domains for*<br>**required field**<br>you can set up to 1000 domains, subdomains or webpages<br>the domain or subdomain should be specified without `https://` and `www.`<br>the page should be specified with absolute URL (including `http://` or `https://`)<br>example:<br>`"targets": [<br> "forbes.com",<br> "cnn.com",<br> "bbc.com",<br> "yelp.com",<br> "https://www.apple.com/iphone/",<br> "https://ahrefs.com/blog/",<br> "ibm.com",<br> "https://variety.com/",<br> "https://stackoverflow.com/",<br> "www.trustpilot.com"<br>]` |
| `date_from` | string | *starting date of the time range*<br>optional field<br>this field indicates the date which will be used as a threshold for new and lost referring domains;<br>the referring domains that appeared in our index after the specified date will be considered as new;<br>the referring domains that weren’t found after the specified date, but were present before, will be considered as lost;<br>default value: today’s date -(minus) one month;<br>e.g. if today is `2021-10-13`, default `date_from` will be `2021-09-13`.<br>**minimum value equals today’s date -(minus) one year;**<br>e.g. if today is `2021-10-13`, minimum `date_from` will be `2020-10-13`.<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2021-01-01"` |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `items_count` | integer | *the number of results returned in the `items` array* |
| `**items**` | array | *contains relevant backlinks and referring domains data* |
| `target` | string | *domain, subdomain or webpage from a POST array*<br> |
| `new_referring_domains` | integer | *number of new referring domains*<br>number of new referring domains pointing to the `target`<br> |
| `lost_referring_domains` | integer | *number of lost referring domains*<br>number of lost referring domains of the `target`<br> |
| `new_referring_main_domains` | integer | *number of new referring main domains pointing to the `target`*<br> |
| `lost_referring_main_domains` | integer | *number of lost referring main domains pointing to the `target`*<br> |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Bulk Pages Summary
*Source: [https://docs.dataforseo.com/v3/backlinks/bulk_pages_summary/live/](https://docs.dataforseo.com/v3/backlinks/bulk_pages_summary/live/)*
#### Bulk Pages Summary

This endpoint will provide you with a comprehensive overview of backlinks and related data for a bulk of up to 1000 pages, domains, or subdomains. If you indicate a single page as a target, you will get comprehensive summary data on all backlinks for that page.

POSThttps://api.dataforseo.com/v3/backlinks/bulk_pages_summary/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/backlinks/backlinks) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `targets` | array | *domains, subdomains or webpages to get summary data for*<br>**required field**<br>a domain or a subdomain should be specified without `https://` and `www.`<br>a page should be specified with absolute URL (including `http://` or `https://`)<br>you can specify up to 1000 pages, domains, or subdomains in each request.<br>**note that the URLs you set in a single request cannot belong to more than 100 different domains**. |
| `include_subdomains` | boolean | *indicates if the subdomains of the `target` will be included in the search*<br>optional field<br>if set to `false`, the subdomains will be ignored<br>default value: `true` |
| `rank_scale` | string | *defines the scale used for calculating and displaying the `rank`, `domain_from_rank`, and `page_from_rank` values*<br>optional field<br>you can use this parameter to choose whether rank values are presented on a 0–100 or 0–1000 scale<br>possible values:<br>`one_hundred` — rank values are displayed on a 0–100 scale<br>`one_thousand` — rank values are displayed on a 0–1000 scale<br>default value: `one_thousand`<br>learn more about how this parameter works and how ranking metrics are calculated in [this Help Center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api#rank_scale) |
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
| `total_count` | integer | *total number of relevant items in the database*<br> |
| `items_count` | integer | *number of items in the results array*<br> |
| **`items`** | array | *items array*<br> |
| `type` | string | * type of element = **‘backlinks_page_summary’*** |
| `url` | string | *page URL* |
| `rank` | integer | *page rank*<br>rank of the page on the `target` website<br>`rank` is calculated based on the method for node ranking in a linked database – a principle used in the original Google PageRank algorithm<br>learn more about the metric and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |
| `main_domain_rank` | integer | *rank of the main domain*<br>rank of the main domain is calculated based on the method for node ranking in a linked database – a principle used in the original Google PageRank algorithm<br>learn more about the metric and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |
| `backlinks` | integer | *number of backlinks*<br> |
| `first_seen` | string | *date and time when our crawler found a backlink to this page for the first time*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `lost_date` | string | *date and time when the last backlink to this page was lost*<br>indicates the date and time when our crawler visited the page and it responded with 4xx or 5xx status code or the last backlink was removed<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2017-01-24 13:20:59 +00:00` |
| `backlinks_spam_score` | integer | *average spam score of the backlinks pointing to the page*<br>learn more about how the metric is calculated on [this help center page](https://dataforseo.com/help-center/what-is-spam-score-and-how-is-it-calculated) |
| `broken_backlinks` | integer | *number of broken backlinks*<br>number of broken backlinks pointing to the page |
| `broken_pages` | integer | *number of broken pages*<br>number of pages that respond with 4xx or 5xx status codes where backlinks are pointing to |
| `referring_domains` | integer | *indicates the number domains referring to the page*<br> |
| `referring_domains_nofollow` | integer | *number of domains pointing at least one nofollow link to the `target`*<br> |
| `referring_main_domains` | integer | *indicates the number of referring main domains*<br> |
| `referring_main_domains_nofollow` | integer | *number of main domains pointing at least one nofollow link to the `target`* |
| `referring_ips` | integer | *number of referring IP addresses*<br>number of IP addresses pointing to this page<br> |
| `referring_subnets` | integer | *number of referring subnetworks*<br> |
| `referring_pages` | integer | *indicates the number of pages pointing to the relevant `url`*<br> |
| `referring_pages_nofollow` | integer | *number of referring pages pointing at least one nofollow link to the `target`* |
| `referring_links_tld` | object | *top-level domains of the referring links*<br>contains top level domains and referring link count per each<br> |
| `referring_links_types` | object | *types of referring links*<br>indicates the types of the referring links and link count per each type<br>possible values:<br>`anchor`, `image`, `link`, `meta`, `canonical`, `alternate`, `redirect`<br> |
| `referring_links_attributes` | object | *link attributes of the referring links*<br>indicates link attributes of the referring links and link count per each attribute<br> |
| `referring_links_platform_types` | object | *types of referring platforms*<br>indicates referring platform types and and link count per each platform<br>possible values: `cms`, `blogs`, `ecommerce`, `message-boards`, `wikis`, `news`, `organization` |
| `referring_links_semantic_locations` | object | *semantic locations of the referring links*<br>indicates semantic elements in HTML where the referring links are located and link count per each semantic location<br>you can get the full list of semantic elements [here](https://www.w3schools.com/html/html5_semantic_elements.asp)<br>examples:<br>`article`, `section`, `footer` |
| `referring_links_countries` | object | *ISO country codes of the referring links*<br>indicates ISO country codes of the domains where the referring links are located and the link count per each country<br> |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---
