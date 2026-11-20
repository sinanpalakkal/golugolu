from django.shortcuts import render
from django.db.models import F
from django.http import Http404

from .models import SearchTrend

import random
import json

from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


# ==========================================
# WEBSITE DATABASE
# ==========================================

WEBSITES = [

    ("Knowledge Hub", "knowledgehub.com", "knowledge-hub"),
    ("6K Pedia", "6kpedia.com", "6k-pedia"),
    ("6K Labs", "6klabs.com", "6k-labs"),
    ("6K Hub", "6khub.com", "6k-hub"),
    ("Golugolu", "golugolu.com", "golugolu"),
    ("The Mystery Files", "mysteryfiles.com", "mystery-files"),
    ("Daily Discoveries", "dailydiscoveries.com", "daily-discoveries"),
    ("Internet Research Center", "researchcenter.com", "research-center"),
    ("Unknown Facts", "unknownfacts.com", "unknown-facts"),
    ("The Digital Library", "digitallibrary.com", "digital-library"),
    ("Random Wikipedia", "randompedia.com", "random-wikipedia"),
    ("Curiosity Zone", "curiosityzone.com", "curiosity-zone"),
    ("The Information Lab", "informationlab.in", "information-lab")

]


# ==========================================
# COMMON CATEGORY PAGE DATA
# ==========================================

def category_context(request):

    query = request.GET.get('q', '').strip()[:255]

    return {

        'query': query,

        'trending': SearchTrend.objects.order_by(
            '-search_count'
        )[:5],

        'history': request.session.get(
            'search_history', []
        )

    }


# ==========================================
# AI OVERVIEW GENERATOR
# ==========================================

def generate_overview(query):

    overviews = [

        f"You searched for '{query}'. Our experts investigated this matter extensively. Unfortunately, they found absolutely nothing useful. 😂",

        f"Regarding '{query}', we conducted a highly unnecessary investigation. The results are as confusing as your search history.",

        f"'{query}' is an interesting topic. Unfortunately, our research department has decided that ignorance is happiness.",

        f"After searching the entire internet for '{query}', we can confidently say that you could have spent this time doing something else.",

        f"We received your question about '{query}'. Our search engine is currently questioning its existence."

    ]

    return random.choice(overviews)


# ==========================================
# HOME PAGE
# ==========================================

def home(request):

    trending = SearchTrend.objects.order_by(
        '-search_count'
    )[:5]

    history = request.session.get(
        'search_history', []
    )

    return render(request, 'search/home.html', {

        'trending': trending,

        'history': history

    })


# ==========================================
# ABOUT PAGE
# ==========================================

def about(request):

    return render(
        request,
        'search/about.html'
    )


# ==========================================
# SEARCH RESULTS - ALL
# ==========================================

def results(request):

    query = request.GET.get('q', '').strip()[:255]

    results_list = []

    overview = ""

    if query:

        # SAVE TRENDING SEARCH

        key = query.casefold()

        trend, created = SearchTrend.objects.get_or_create(

            query_key=key,

            defaults={
                'display_query': query,
                'search_count': 1
            }

        )

        if not created:

            SearchTrend.objects.filter(

                pk=trend.pk

            ).update(

                search_count=F('search_count') + 1,

                display_query=query

            )


        # SAVE SEARCH HISTORY

        history = request.session.get(
            'search_history', []
        )

        history = [

            item for item in history

            if item.casefold() != key

        ]

        history.insert(0, query)

        request.session['search_history'] = history[:10]


        # GENERATE AI OVERVIEW

        overview = generate_overview(query)


        # GENERATE SEARCH RESULTS

        result_templates = [

            (
                f"Everything you need to know about {query}",

                f"We spent 47 hours researching {query}. Then we realized we had absolutely no idea what we were doing."
            ),

            (
                f"The Ultimate Guide to {query}",

                "Step 1: Read this result. Step 2: Realize this website is useless. Step 3: Continue scrolling."
            ),

            (
                f"Experts explain {query}",

                "Our team of highly unqualified experts has reached a conclusion: Nobody knows anything."
            ),

            (
                f"Why everyone is searching for {query}",

                "Because apparently people have nothing better to do. Welcome to the club!"
            ),

            (
                f"{query} - Everything you should NOT know",

                "This information is completely unnecessary, potentially confusing and absolutely useless."
            ),

            (
                f"Breaking News: {query}",

                "Scientists are confused. Researchers are sleeping. Our search engine is doing absolutely nothing."
            ),

            (
                f"Top 10 facts about {query}",

                "We had 10 facts ready, but unfortunately, all of them disappeared."
            ),

            (
                f"Can {query} change your life?",

                "Possibly. But visiting this website definitely won't."
            ),

            (
                f"The truth about {query}",

                "We promised to reveal the truth. Unfortunately, we couldn't find it."
            )

        ]


        selected_results = random.sample(
            result_templates, 5
        )

        selected_websites = random.sample(
            WEBSITES, 5
        )


        for (title, description), (site_name, site_url, site_slug) in zip(

            selected_results,

            selected_websites

        ):

            results_list.append({

                'title': title,

                'description': description,

                'site_name': site_name,

                'site_url': site_url,

                'site_slug': site_slug

            })


    return render(request, 'search/results.html', {

        'query': query,

        'results_list': results_list,

        'overview': overview,

        'trending': SearchTrend.objects.order_by(
            '-search_count'
        )[:5],

        'history': request.session.get(
            'search_history', []
        ),

    })


# ==========================================
# AI MODE PAGE
# ==========================================

def ai_mode(request):

    context = category_context(request)

    query = context['query']

    overview = generate_overview(query) if query else ""

    context['overview'] = overview

    return render(
        request,
        'search/ai_mode.html',
        context
    )


# ==========================================
# IMAGES PAGE - OPENVERSE API
# ==========================================

def images(request):

    context = category_context(request)

    query = context['query']

    image_results = []

    image_error = None

    if query:

        try:

            # OPENVERSE IMAGE API

            api_url = "https://api.openverse.org/v1/images/"

            params = {

                'q': query,

                'page_size': 24,

                'page': 1

            }

            url = api_url + "?" + urlencode(params)

            api_request = Request(

                url,

                headers={
                    'User-Agent': 'GolugoluSearch/1.0'
                }

            )

            with urlopen(
                api_request,
                timeout=15
            ) as response:

                data = json.loads(
                    response.read().decode('utf-8')
                )


            # EXTRACT IMAGE INFORMATION

            for item in data.get('results', []):

                image_url = item.get('thumbnail')

                if not image_url:
                    image_url = item.get('url')

                if not image_url:
                    continue

                image_results.append({

                    'title': item.get(
                        'title',
                        'Untitled Image'
                    ),

                    'image_url': image_url,

                    'original_url': item.get(
                        'url',
                        image_url
                    ),

                    'creator': item.get(
                        'creator',
                        'Unknown Creator'
                    ),

                    'license': item.get(
                        'license',
                        'Unknown'
                    ),

                    'source_url': item.get(
                        'foreign_landing_url',
                        ''
                    )

                })


        except (HTTPError, URLError, TimeoutError, ValueError):

            image_error = (
                "We couldn't load images right now. "
                "Please try again later."
            )


    context.update({

        'image_results': image_results,

        'image_error': image_error

    })


    return render(
        request,
        'search/images.html',
        context
    )


# ==========================================
# VIDEOS PAGE
# ==========================================

def videos(request):

    context = category_context(request)

    # VIDEO SEARCH WILL BE IMPLEMENTED LATER

    context.update({

        'video_results': [],

        'video_error': None

    })

    return render(
        request,
        'search/videos.html',
        context
    )


# ==========================================
# SHOPPING PAGE
# ==========================================

def shopping(request):

    context = category_context(request)

    # SHOPPING SEARCH WILL BE IMPLEMENTED LATER

    context.update({

        'shopping_results': [],

        'shopping_error': None

    })

    return render(
        request,
        'search/shopping.html',
        context
    )


# ==========================================
# NEWS PAGE
# ==========================================

def news(request):

    context = category_context(request)

    # NEWS SEARCH WILL BE IMPLEMENTED LATER

    context.update({

        'news_results': [],

        'news_error': None

    })

    return render(
        request,
        'search/news.html',
        context
    )


# ==========================================
# DYNAMIC FAKE WEBSITES
# ==========================================

def site_detail(request, site_slug):

    websites = {

        "knowledge-hub": "Knowledge Hub",
        "6k-pedia": "6K Pedia",
        "6k-labs": "6K Labs",
        "6k-hub": "6K Hub",
        "golugolu": "Golugolu",
        "mystery-files": "The Mystery Files",
        "daily-discoveries": "Daily Discoveries",
        "research-center": "Internet Research Center",
        "unknown-facts": "Unknown Facts",
        "digital-library": "The Digital Library",
        "random-wikipedia": "Random Wikipedia",
        "curiosity-zone": "Curiosity Zone",
        "information-lab": "The Information Lab"

    }

    site_name = websites.get(site_slug)

    if not site_name:

        raise Http404("This useless website does not exist!")


    query = request.GET.get(
        'q',
        'Something Unnecessary'
    )[:255]


    title = request.GET.get(
        'title',
        'Welcome to our website'
    )[:255]


    description = request.GET.get(
        'description',
        'We have absolutely nothing useful to offer.'
    )[:1000]


    funny_articles = [

        "Our researchers spent 10 years investigating this topic. They forgot what they were investigating.",

        "According to our highly unreliable sources, this information may or may not be correct.",

        "Scientists are currently sleeping. Please try again tomorrow.",

        "This information has been verified by absolutely nobody.",

        "Our artificial intelligence has decided to take a vacation.",

        "We asked 100 experts. Unfortunately, all of them were confused.",

        "This discovery is so useless that even Google refused to index it.",

        "Breaking news: Nothing has happened. Thank you for your attention.",

        "Our research team has successfully failed to find anything useful.",

        "The answer is somewhere on the internet. Unfortunately, we don't know where."

    ]

    articles = random.sample(
        funny_articles, 4
    )


    website_taglines = {

        "knowledge-hub": "Where knowledge goes to get confused.",

        "6k-pedia": "The encyclopedia of absolutely unnecessary knowledge.",

        "6k-labs": "Conducting experiments nobody requested.",

        "6k-hub": "Your destination for questionable information.",

        "golugolu": "Search less. Get confused more.",

        "mystery-files": "Solving mysteries that don't exist.",

        "daily-discoveries": "Discovering absolutely nothing every day.",

        "research-center": "Researching things nobody cares about.",

        "unknown-facts": "Facts that should have remained unknown.",

        "digital-library": "A library full of things you don't need.",

        "random-wikipedia": "Wikipedia's extremely confused cousin.",

        "curiosity-zone": "Curiosity killed the search engine.",

        "information-lab": "100% useless research."

    }

    tagline = website_taglines.get(
        site_slug,
        "The internet's most questionable source of information."
    )


    return render(request, 'search/fake_site.html', {

        'site_name': site_name,

        'site_slug': site_slug,

        'tagline': tagline,

        'query': query,

        'title': title,

        'description': description,

        'articles': articles

    })