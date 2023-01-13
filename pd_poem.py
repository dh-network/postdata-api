from util import shorthash
from poem import Poem
from sparql import DB, SparqlResults
from pd_author import PostdataAuthor
from pd_stardog_queries import PdStardogQuery, PoemTitle, PoemCreationYear, PoemAuthorUris, PoemAutomaticScansionUri, \
    PoemCountStanzas, PoemCountLines, PoemCountWords, PoemCountLinesInStanzas, PoemRhymeSchemesOfStanzas, \
    PoemCountSyllables, PoemCountSyllablesInStanzas, PoemCountWordsInStanzas, PoemGrammaticalStressPatternsInStanzas, \
    PoemMetricalPatternsInStanzas

# TODO: maybe streamline the SPARQL Query execution of the basic queries as done with get_automatic_scansion_uri
# The methods returning basic metadata have somewhat redundancies. They all check if db connection is available,...
# I tried to remove them with a  wrapper function "__execute_sparql_query" BUT the queries executed with this function
# are initialized in the function that calls the "__execute_sparql_query" function; whereas the basic metadata queries
# are instantiated in the __init. So there might be some more tinkering involved.
# If the query is not instantiated on the class level, we have no chance to use the rich possibilities, e.g call the
# .explain() method. This is possible with the basic metadata queries, which are available,
# e.g. poem.sparql_creation_year.explain(); in the case of the "__execute_sparql_query" construct, this doesn't work,
# because the query "lives" only in the function, e.g. in "get_automatic_scansion_uri" "query". We might need some
# third (hybrid) variant, that streamlines code, but also allows for exploiting the query's methods.


class PostdataPoem(Poem):
    """POSTDATA Poem

    Attributes:
        uri (str): URI of the poem in the POSTDATA Knowledge Graph.
        id (str): ID generated by creating an 8 character shortened md5 hash of the URI.
        name (str): Name of the poem. A combination of author and title.
        database (DB): Database connection. Instance of class DB.
        author_uris (list): URIs of authors of a poem.
        authors (list): Instances of class PostdataAuthor.
        automatic_analysis (dict): Analysis based on an automatic scansion.
    """

    # uri of the poem
    uri = None

    # Database connection
    database = None

    # ID generated by creating an 8 character shortened md5 hash of the URI
    id = None

    # Name of the Poem, a combination of author and title
    name = None

    # View of the poem in POSTDATAs Poetry Lab
    poetry_lab_url = None

    # URIs of authors
    author_uris = None

    # Authors
    authors = None

    # Analysis:
    # TODO: Handle the scansions
    # Analysis that is based on an AutomaticScansion
    automatic_analysis = None

    def __init__(self, uri: str = None, database: DB = None):
        """Initialize poem

        Args:
            uri (str): URI of a poem.
            database (DB): connection to a triple store. Use instance of class DB.
        """
        if uri:
            self.uri = uri

        # Generate additional identifiers
        if self.uri:
            # a poem can be identified by the full URI or a shorted md5 hash. The corpus has a lookup method to
            # look up the full uri by this identifier
            self.__generate_id_by_uri()
            # poem name: author and poem/title part joined by "_"
            self.__generate_name_by_uri()

        if database:
            self.database = database

        # SPARQL Queries:
        # Title of the Poem – used in: get_title()
        self.sparql_title = PoemTitle()
        # Year of Creation – used in: get_creation_year()
        self.sparql_creation_year = PoemCreationYear()
        # URIs of Authors – used in: get_author_uris()
        self.sparql_author_uris = PoemAuthorUris()

    def __generate_id_by_uri(self) -> bool:
        """Helper method to generate a short md5 hash from the URI

        Create a md5 hash and trunctate it. This is handled by the shorthash function from the util module.
        Attention: This is aligned to PostdataCorpus method __generate_poem_id_by_poem_uri; if changed independently,
        the lookup of poems won't work.

        Returns:
            bool: True if successful.
        """
        if self.uri:
            self.id = shorthash(self.uri)
            return True

    def __generate_name_by_uri(self) -> bool:
        """Helper method to generate a poem name

        Extract author and title/poem part from the URI and join them with "_" and
        store it to the class' "name" attribute.

        The uri "http://postdata.linhd.uned.es/resource/pw_juana-ines-de-la-cruz_sabras-querido-fabio" will result in
        "juana-ines-de-la-cruz_sabras-querido-fabio"

        Returns:
            bool: True if successful.
        """
        if self.uri:
            author_poem = self.__split_uri_in_author_poem_parts()
            self.name = "_".join(author_poem)
            return True

    def get_title(self) -> str:
        """Get the title of the poem.

        Uses a SPARQL Query of class "PoemTitle" of the module "pd_stardog_queries".

        Returns:
            str: Title of the poem.
        """
        if self.title:
            return self.title
        else:
            if self.database:
                # Use the SPARQL Query of class "PoemTitle" (set as attribute of this class)
                if self.uri:
                    # inject the URI of the poem into the query
                    self.sparql_title.inject([self.uri])
                else:
                    raise Exception("No URI of the poem specified. Can not get any attributes.")
                self.sparql_title.execute(self.database)
                title_list = self.sparql_title.results.simplify()
                if len(title_list) == 1:
                    self.title = title_list[0]
                    return self.title
                else:
                    raise Exception("Poem has multiple titles. Not implemented.")
            else:
                raise Exception("Database Connection not available.")

    def get_creation_year(self) -> str:
        """Get the year of creation of a poem.

        Uses a SPARQL Query of class "PoemCreationYear" of the module "pd_stardog_queries".

        Attention: If there are multiple values, only one (the first of the list returned by the query) is returned.

        Returns:
            str: Year of the creation. It must not be assumed that the returned string value can be automatically cast
                into a date data type, because the returned value might also contain a marker of uncertainty, e.g.
                "¿?", but also "¿Ca. 1580?" or "¿1603?".
        TODO: find out, which modifiers of uncertainty might be returned.
        """
        if self.creation_year:
            return self.creation_year
        else:
            if self.database:
                # Use the SPARQL Query of class "PoemCreationYear" (set as attribute of this class)
                if self.uri:
                    # inject the URI of the poem into the query
                    self.sparql_creation_year.inject([self.uri])
                else:
                    raise Exception("No URI of the poem specified. Can not get any attributes.")
                self.sparql_creation_year.execute(self.database)
                data = self.sparql_creation_year.results.simplify()
                if len(data) == 0:
                    self.creation_year = None
                elif len(data) == 1:
                    self.creation_year = data[0]
                else:
                    raise Exception("Multiple values for creation year. Not implemented.")

                return self.creation_year

            else:
                raise Exception("Database Connection not available.")

    def __split_uri_in_author_poem_parts(self) -> list:
        """Helper method to split the poem URL into an author- and a poem part.

        The uri "http://postdata.linhd.uned.es/resource/pw_juana-ines-de-la-cruz_sabras-querido-fabio" is split into:
        "juana-ines-de-la-cruz" (author part) and "sabras-querido-fabio" (poem part)

        Returns:
            list: First item is the author part, second the poem part.
        """
        if self.uri:
            author_part = self.uri.split("_")[1]
            poem_part = self.uri.split("_")[2]
            return [author_part, poem_part]
        else:
            raise Exception("URI of the poem has not been defined.")

    def get_poetry_lab_url(self, base_url: str = "http://poetry.linhd.uned.es:3000", lang: str = "en") -> str:
        """Convert the URI of a poem into a link to POSTDATAs Poetry Lab Platform

        Args:
            base_url: Base URL of POSTDATAs Poetry Lab. Defaults to "http://poetry.linhd.uned.es:3000".
            lang (str): language version of Poetry Lab. Allowed values "en", "es". Defaults to "en".

        Returns:
            str: URL to access the poem in Poetry Lab.
        """
        if self.poetry_lab_url:
            return self.poetry_lab_url
        else:
            # use the function to split up the URI into an author and a poem part
            author_poem = self.__split_uri_in_author_poem_parts()
            author_part = author_poem[0]
            poem_part = author_poem[1]
            self.poetry_lab_url = f"{base_url}/{lang}/author/{author_part}/poetic-work/{poem_part}"
            return self.poetry_lab_url

    def get_author_uris(self) -> list:
        """Get URIs of Authors of a Poem.

        Uses a SPARQL Query of class "PoemAuthorUris" of the module "pd_stardog_queries".

        Returns:
            list: URIs of Authors.
        """
        if self.author_uris:
            return self.author_uris
        else:
            if self.database:
                # Use the SPARQL Query of class "PoemAuthorUris" (set as attribute of this class)
                if self.uri:
                    # inject the URI of the poem into the query
                    self.sparql_author_uris.inject([self.uri])
                else:
                    raise Exception("No URI of the poem specified. Can not get any attributes.")
                self.sparql_author_uris.execute(self.database)
                data = self.sparql_author_uris.results.simplify()
                if len(data) == 0:
                    self.author_uris = None
                else:
                    self.author_uris = data

                return self.author_uris

            else:
                raise Exception("Database Connection not available.")

    def load_authors(self) -> bool:
        """Load Authors of a Poem.

        For each of the URIs in author_uris, a new instance of "PostdataAuthor" is created and added to the list
        of authors "self.authors".

        Returns:
            bool: True if successful. "False" if there are no authors in the data.
        """
        if self.author_uris:
            pass
        else:
            # Make sure, that there are author uris
            self.get_author_uris()

        if self.author_uris:
            self.authors = []
            for uri in self.author_uris:
                author = PostdataAuthor(uri=uri, database=self.database)
                self.authors.append(author)
            return True
        else:
            # There are no authors in the data
            self.authors = None
            return False

    def get_metadata(self, include_authors: bool = False, include_analysis: bool = False) -> dict:
        """Serialize (basic) metadata of a poem.

        Request only the necessary attributes of a poem, e.g. to use in an instance
        of "PostdataCorpus" when viewing all poems.

        Args:
            include_authors (bool): Include author information. Defaults to False.
            include_analysis (bool): Include the analysis of a poem derived from an automatic scansion.
                Defaults to False.

        Returns:
            dict: (Basic) Metadata on a poem.
        """

        metadata = dict(
            id=self.id,
            uri=self.uri,
            name=self.name,
            source=self.get_poetry_lab_url(),
            sourceUri="POSTDATA Poetry Lab"
        )

        if include_authors:
            if self.load_authors():
                metadata["authors"] = list()
                for author in self.authors:
                    metadata["authors"].append(author.get_metadata())

        if include_analysis:
            metadata["analysis"] = self.get_analysis()

        return metadata

    # The following methods return results of an automatic analysis of a poem resulting in an automatedScansion
    # We ignore the manual scansion and focus of the automatic analysis only. The SPARQL Queries are initialized only
    # when the analysis is run. This is somewhat inconsistent to what is done with the Queries, that return basic
    # metadata; ideally, we would model the analysis as a separate class "Scansion" (this would be closer to POSTDATAs
    # approach, but then all the already working queries, that start from a poem URI would have to be re-written. For
    # the demonstrator, this is not feasible, but might become relevant at some later stage.)

    def __execute_sparql_query(self, sparql_query: PdStardogQuery) -> SparqlResults:
        """Wrapper for a SPARQL Query.

        This method tries to streamline the process of checking, if a query can be executed and preparing the query.

        Returns:
            SparqlResults: Results of the SPARQL Query as instance of class "SparqlResults"
        """
        if self.database:
            if self.uri:
                sparql_query.inject([self.uri])
            else:
                raise Exception("No URI of the poem specified. Can not get any attributes.")
            sparql_query.execute(self.database)
            return sparql_query.results
        else:
            raise Exception("Database Connection not available.")

    def __group_feature_by_stanzas(self,
                                   simplified_sparql_results: list,
                                   stanza_number_field_key: str = "StanzaNo",
                                   value_field_key: str = "count",
                                   value_datatype: str = "int"
                                   ) -> list:
        """Group Values/Features by Stanzas.

        This helper method groups features/values retrieved by a SPARQL Query into Stanzas (List of Lists), e.g.
        "[[11, 11, 11, 11], [11, 11, 11, 11], [11, 11, 11], [11, 11, 11]]". It is expected, that the query returns
        information on the number of the stanza. A field must be the Stanza Number. The key of this field can be set
        with the keyword argument "stanza_number_field_key". The value/feature that should be grouped can be
        accessed by taking the value from the field with the key contained in the keyword argument "value_field_key". If
        the value should be cast to an integer, the keyword argument "value_datatype" should be set to "int", in all
        other cases it will be considered a string.
        It expects that the values/features are ordered by absolute line number.

        Args:
            simplified_sparql_results (list): SPARQL result after simplify().
            stanza_number_field_key (str): Key of the field containing the Stanza Number. Defaults to "StanzaNo".
            value_field_key (str): Key of the field that contains the value/the feature.
            value_datatype (str): Cast value to a datatype. Defaults to "int" for Integer. Everything else will be
                cast to a string.

        Returns:
            list: Features grouped into stanzas.
        """
        # Sorry, even worse Spaghetti-Code follows from here.

        grouped_results = []
        stanza = []
        current_stanza = 0

        for binding in simplified_sparql_results:
            # print(binding)
            stanza_number = binding[stanza_number_field_key]
            # print("Current stanza:" + stanza_number)
            if value_datatype == "int" or value_datatype == "Integer":
                value = int(binding[value_field_key])
            elif value_datatype == "str" or value_datatype == "String":
                value = str(binding[value_field_key])
            else:
                value = binding[value_field_key]

            if current_stanza == stanza_number:
                # print("appending to stanza" + str(value))
                stanza.append(value)
            else:
                # next stanza
                # print("Next stanza!")
                if int(current_stanza) > 0:
                    # this should only by done when we reached stanza two
                    grouped_results.append(stanza)
                # set this as current stanza
                current_stanza = stanza_number
                # reset the stanza
                # print("resetting the stanza")
                stanza = list()
                # print("appending value to stanza after reset" + str(value))
                stanza.append(value)

        # append the last stanza
        grouped_results.append(stanza)

        return grouped_results

    def get_automatic_scansion_uri(self) -> str:
        """URI of an Automatic Scansion.

        Uses a SPARQL Query of class "PoemAutomaticScansionUri" of the module "pd_stardog_queries".

        Returns:
            str: URI of an automatic scansion.
        """
        query = PoemAutomaticScansionUri()
        results = self.__execute_sparql_query(query)
        # TODO: make sure, that there is only one URI of an Automatic Scansion. In Theory there could be more, also with
        # contradicting results
        return results.simplify()[0]

    def get_number_of_stanzas(self) -> int:
        """Count Stanzas of a Poem.

        Uses a SPARQL Query of class "PoemCountStanzas" of the module "pd_stardog_queries".

        Returns:
            int: Number of Stanzas
        """
        query = PoemCountStanzas()
        results = self.__execute_sparql_query(query)
        mapping = {"count": {"datatype": "int"}}
        return results.simplify(mapping=mapping)[0]

    def get_number_of_lines(self) -> int:
        """Count Lines of a Poem.

        Uses a SPARQL Query of class "PoemCountLines" of the module "pd_stardog_queries".

        Returns:
            int: Number of Lines.
        """
        query = PoemCountLines()
        results = self.__execute_sparql_query(query)
        mapping = {"count": {"datatype": "int"}}
        return results.simplify(mapping=mapping)[0]

    def get_number_of_words(self) -> int:
        """Count Words of a Poem.

        Uses a SPARQL Query of class "PoemCountWords" of the module "pd_stardog_queries".

        Returns:
            int: Number of Words.
        """
        query = PoemCountWords()
        results = self.__execute_sparql_query(query)
        mapping = {"count": {"datatype": "int"}}
        return results.simplify(mapping=mapping)[0]

    def get_number_of_syllables(self, syllable_type: str = "metrical") -> int:
        """Count Syllables of a Poem.

        Uses a SPARQL Query of class "PoemCountSyllables" of the module "pd_stardog_queries". The query has two
        variables: The first one is the URI of the poem, the second one must be replaced with the property connecting
        the line to the count of syllables of a certain type: "pdp:hasMetricalSyllable" or pdp:hasGrammaticalSyllable.

        Args:
            syllable_type (str): Type of syllable ("grammatical" or "metrical"). Defaults to "metrical".

        Returns:
            int: Number of metrical or grammatical syllables.

        """
        # set the type of syllable by replacing the second variable in the query
        # can be "pdp:hasGrammaticalSyllable" or "pdp:hasMetricalSyllable"
        if syllable_type == "metrical":
            syllable_type_prop = "pdp:hasMetricalSyllable"
        elif syllable_type == "grammatical":
            syllable_type_prop = "pdp:hasGrammaticalSyllable"
        else:
            raise Exception("Syllable Type is not valid.")

        query = PoemCountSyllables()
        if self.database:
            if self.uri:
                query.inject([self.uri, syllable_type_prop])
            else:
                raise Exception("No URI of the poem specified. Can not get any attributes.")
            query.execute(self.database)
        else:
            raise Exception("Database Connection not available.")

        mapping = {"count": {"datatype": "int"}}
        return query.results.simplify(mapping=mapping)[0]

    def get_number_of_lines_in_stanzas(self) -> list:
        """Count lines per Stanza

        Uses a SPARQL Query of class "PoemCountLinesInStanzas" of the module "pd_stardog_queries".

        Returns:
            list: Number of lines for each stanza.
        """
        query = PoemCountLinesInStanzas()
        results = self.__execute_sparql_query(query)
        mapping = {"count": {"datatype": "int"}}
        return results.simplify(mapping=mapping)

    def get_rhyme_schemes_of_stanzas(self) -> list:
        """Get Rhyme Scheme per Stanza

        Uses a SPARQL Query of class "PoemRhymeSchemesOfStanzas" of the module "pd_stardog_queries".

        Returns:
            list: Number of rhyme scheme for each stanza.
        """
        query = PoemRhymeSchemesOfStanzas()
        results = self.__execute_sparql_query(query)
        return results.simplify()

    def get_number_of_syllables_in_stanzas(self, syllable_type: str = "metrical") -> list:
        """Count Syllables in a Verse Line in each Stanza

        Uses a SPARQL Query of class "PoemCountSyllablesInStanzas" of the module "pd_stardog_queries". The query has two
        variables: The first one is the URI of the poem, the second one must be replaced with the property connecting
        the line to the count of syllables of a certain type: "pdp:hasMetricalSyllable" or pdp:hasGrammaticalSyllable.

        Args:
            syllable_type (str): Type of syllable ("grammatical" or "metrical"). Defaults to "metrical".

        Returns:
            list: Number of Syllables per Stanza
        """
        # set the type of syllable by replacing the second variable in the query
        # can be "pdp:hasGrammaticalSyllable" or "pdp:hasMetricalSyllable"
        if syllable_type == "metrical":
            syllable_type_prop = "pdp:hasMetricalSyllable"
        elif syllable_type == "grammatical":
            syllable_type_prop = "pdp:hasGrammaticalSyllable"
        else:
            raise Exception("Syllable Type is not valid.")

        query = PoemCountSyllablesInStanzas()
        if self.database:
            if self.uri:
                query.inject([self.uri, syllable_type_prop])
            else:
                raise Exception("No URI of the poem specified. Can not get any attributes.")
            query.execute(self.database)
        else:
            raise Exception("Database Connection not available.")

        # the query returns the counts per line; we group the syllable counts by stanzas
        values_grouped_by_stanzas = self.__group_feature_by_stanzas(
            query.results.simplify(),
            stanza_number_field_key="StanzaNo",
            value_field_key="count",
            value_datatype="int"
        )

        return values_grouped_by_stanzas

    def get_number_of_words_in_stanzas(self) -> list:
        """Count Words in a Verse Line in each Stanza

        Uses a SPARQL Query of class "PoemCountWordsInStanzas" of the module "pd_stardog_queries".

        Returns:
            list: Number of Words per verse line grouped into stanzas

        """
        query = PoemCountWordsInStanzas()
        if self.database:
            if self.uri:
                query.inject([self.uri])
            else:
                raise Exception("No URI of the poem specified. Can not get any attributes.")
            query.execute(self.database)
        else:
            raise Exception("Database Connection not available.")

        # the query returns the counts per line; we group the syllable counts by stanzas
        values_grouped_by_stanzas = self.__group_feature_by_stanzas(
            query.results.simplify(),
            stanza_number_field_key="StanzaNo",
            value_field_key="count",
            value_datatype="int"
        )

        return values_grouped_by_stanzas

    def get_grammatical_stress_patterns_in_stanzas(self) -> list:
        """Get the grammatical stress pattern for each verse line grouped into stanzas.

        Uses a SPARQL Query of class "PoemGrammaticalStressPatternsInStanzas" of the module "pd_stardog_queries".

        Returns:
            list: grammatical stress patterns for each verse line grouped into stanzas.
        """
        query = PoemGrammaticalStressPatternsInStanzas()
        if self.database:
            if self.uri:
                query.inject([self.uri])
            else:
                raise Exception("No URI of the poem specified. Can not get any attributes.")
            query.execute(self.database)
        else:
            raise Exception("Database Connection not available.")

        # the query returns the counts per line; we group the syllable counts by stanzas
        values_grouped_by_stanzas = self.__group_feature_by_stanzas(
            query.results.simplify(),
            stanza_number_field_key="StanzaNumber",
            value_field_key="grammaticalStressPattern",
            value_datatype="str"
        )

        return values_grouped_by_stanzas

    def get_metrical_patterns_in_stanzas(self) -> list:
        """Get the metrical pattern for each verse line grouped into stanzas.

        Uses a SPARQL Query of class "PoemMetricalPatternsInStanzas" of the module "pd_stardog_queries".

        Returns:
            list: metrical patterns for each verse line grouped into stanzas.
        """
        query = PoemMetricalPatternsInStanzas()
        if self.database:
            if self.uri:
                query.inject([self.uri])
            else:
                raise Exception("No URI of the poem specified. Can not get any attributes.")
            query.execute(self.database)
        else:
            raise Exception("Database Connection not available.")

        # the query returns the counts per line; we group the syllable counts by stanzas
        values_grouped_by_stanzas = self.__group_feature_by_stanzas(
            query.results.simplify(),
            stanza_number_field_key="StanzaNumber",
            value_field_key="metricalPattern",
            value_datatype="str"
        )

        return values_grouped_by_stanzas

    def get_analysis(self, scansion_type: str = "automatic"):
        """Return an automatic analysis of a poem."""

        """
        Example:
        
        {'source': {'uri': 'http://postdata.linhd.uned.es/resource/sc_carlos-mendoza_noviembre_disco2-1_1645475669320137'},
 'numOfStanzas': 4,
 'numOfLines': 14,
 'numOfWords': 87,
 'numOfLinesInStanzas': [4, 4, 3, 3],
 'rhymeSchemesOfStanzas': ['abba', 'abba', 'a-a', 'a-a'],
 'numOfMetricalSyllables': 154,
 'numOfGrammaticalSyllables': 166,
 'numOfMetricalSyllablesInStanzas': [[11, 11, 11, 11],
  [11, 11, 11, 11],
  [11, 11, 11],
  [11, 11, 11]],
 'numOfGrammaticalSyllablesInStanzas': [[12, 12, 13, 12],
  [12, 11, 11, 11],
  [11, 11, 12],
  [12, 13, 13]],
 'numOfWordsInStanzas': [[4, 8, 7, 5], [8, 5, 5, 5], [7, 6, 6], [7, 8, 6]],
 'grammaticalStressPatternsInStanzas': [['--+---+---+-',
   '+-+---+-+-+-',
   '-+-+---+---+-',
   '-+----+-+-+-'],
  ['+-+---+---+-', '---+---+-+-', '-+---+---+-', '-+---+---+-'],
  ['++---+---+-', '-+---+---+-', '+---+-+---+-'],
  ['-+---++-+-+-', '--+--+-----+-', '+-+---+----+-']],
 'metricalPatternsInStanzas': [['--+--+---+-',
   '+-+--+-+-+-',
   '+-+--+---+-',
   '-+---+-+-+-'],
  ['+-+--+---+-', '---+---+-+-', '-+---+---+-', '-+---+---+-'],
  ['++---+---+-', '-+---+---+-', '+--+-+---+-'],
  ['-+--++-+-+-', '--+--+---+-', '+-+--+---+-']]}
        """
        if self.automatic_analysis:
            return self.automatic_analysis

        else:

            source = dict(
                uri=self.get_automatic_scansion_uri()
            )

            analysis = dict(
                source=source,
                numOfStanzas=self.get_number_of_stanzas(),
                numOfLines=self.get_number_of_lines(),
                numOfWords=self.get_number_of_words(),
                numOfLinesInStanzas=self.get_number_of_lines_in_stanzas(),
                rhymeSchemesOfStanzas=self.get_rhyme_schemes_of_stanzas(),
                numOfMetricalSyllables=self.get_number_of_syllables(syllable_type="metrical"),
                numOfGrammaticalSyllables=self.get_number_of_syllables(syllable_type="grammatical"),
                numOfMetricalSyllablesInStanzas=self.get_number_of_syllables_in_stanzas(syllable_type="metrical"),
                numOfGrammaticalSyllablesInStanzas=self.get_number_of_syllables_in_stanzas(syllable_type="grammatical"),
                numOfWordsInStanzas=self.get_number_of_words_in_stanzas(),
                grammaticalStressPatternsInStanzas=self.get_grammatical_stress_patterns_in_stanzas(),
                metricalPatternsInStanzas=self.get_metrical_patterns_in_stanzas(),
                )
            self.automatic_analysis = analysis

            return self.automatic_analysis
