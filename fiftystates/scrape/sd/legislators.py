from fiftystates.scrape import NoDataForPeriod
from fiftystates.scrape.legislators import LegislatorScraper, Legislator
from fiftystates.scrape.sd import metadata

import lxml.html


class SDLegislatorScraper(LegislatorScraper):
    state = 'sd'

    def _make_headers(self, url):
        # South Dakota's gzipped responses seem to be broken
        headers = super(SDLegislatorScraper, self)._make_headers(url)
        headers['Accept-Encoding'] = ''

        return headers

    def scrape(self, chamber, term):
        start_year = None
        for term_ in self.metadata['terms']:
            if term_['name'] == term:
                start_year = term_['start_year']
                break
        else:
            raise NoDataForPeriod(term)

        if int(start_year) > 2009:
            self.scrape_legislators(chamber, term)

    def scrape_legislators(self, chamber, term):
        url = "http://legis.state.sd.us/sessions/%s/MemberMenu.aspx" % (
            term)

        if chamber == 'upper':
            search = 'Senate Members'
        else:
            search = 'House Members'

        with self.urlopen(url) as page:
            page = lxml.html.fromstring(page)
            page.make_links_absolute(url)

            for link in page.xpath("//h4[text()='%s']/../div/a" % search):
                name = link.text.strip()

                self.scrape_legislator(name, chamber, term,
                                       link.attrib['href'])

    def scrape_legislator(self, name, chamber, term, url):
        with self.urlopen(url) as page:
            page = lxml.html.fromstring(page)

            party = page.xpath("string(//span[contains(@id, 'Party')])")
            party = party.strip()

            district = page.xpath("string(//span[contains(@id, 'District')])")
            district = district.strip().lstrip('0')

            occupation = page.xpath(
                "string(//span[contains(@id, 'Occupation')])")
            occupation = occupation.strip()

            legislator = Legislator(term, chamber, district, name,
                                    party=party, occupation=occupation)
            legislator.add_source(url)
            self.save_legislator(legislator)
