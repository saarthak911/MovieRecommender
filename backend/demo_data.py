"""Small DEMO catalogue so the site runs before you add the real TMDB files.

Titles are real films, but the one-line descriptions are written for this demo and
the ratings/vote counts are only illustrative. Put the real Kaggle CSVs in ../data
and the app will use them automatically instead of this list.
"""


def m(id_, title, year, genres, overview, keywords, cast, director, rating, votes):
    return {
        "id": id_,
        "title": title,
        "year": year,
        "genres": genres.split("|"),
        "overview": overview,
        "keywords": keywords.split(","),
        "cast": cast.split(","),
        "director": director,
        "vote_average": rating,
        "vote_count": votes,
    }


DEMO = [
    m(1, "Inception", 2010, "Action|Science Fiction|Thriller", "A thief who steals secrets from dreams is hired to plant an idea in a target's mind.", "dream,heist,subconscious,mind bending", "Leonardo DiCaprio,Joseph Gordon-Levitt,Elliot Page", "Christopher Nolan", 8.3, 31000),
    m(2, "Interstellar", 2014, "Adventure|Drama|Science Fiction", "Astronauts travel through a wormhole searching for a new home for humanity.", "space,wormhole,time dilation,survival", "Matthew McConaughey,Anne Hathaway,Jessica Chastain", "Christopher Nolan", 8.2, 28000),
    m(3, "The Dark Knight", 2008, "Action|Crime|Drama|Thriller", "Batman faces a chaotic criminal mastermind who pushes Gotham to the edge.", "superhero,vigilante,joker,gotham", "Christian Bale,Heath Ledger,Aaron Eckhart", "Christopher Nolan", 8.4, 30000),
    m(4, "The Matrix", 1999, "Action|Science Fiction", "A hacker discovers his reality is a simulation and joins a rebellion against its machine rulers.", "simulation,hacker,rebellion,virtual reality", "Keanu Reeves,Laurence Fishburne,Carrie-Anne Moss", "Lana Wachowski", 8.1, 22000),
    m(5, "Blade Runner 2049", 2017, "Science Fiction|Drama|Mystery", "A young blade runner uncovers a secret that could plunge what remains of society into chaos.", "replicant,dystopia,android,future noir", "Ryan Gosling,Harrison Ford,Ana de Armas", "Denis Villeneuve", 7.6, 11000),
    m(6, "Mad Max: Fury Road", 2015, "Action|Adventure|Science Fiction", "In a desert wasteland a drifter and a rebel warrior race across the sands to escape a tyrant.", "chase,post apocalyptic,desert,road", "Tom Hardy,Charlize Theron,Nicholas Hoult", "George Miller", 7.6, 19000),
    m(7, "Dune", 2021, "Science Fiction|Adventure", "A gifted young heir must protect a desert planet and its precious resource from rival houses.", "desert planet,prophecy,empire,spice", "Timothée Chalamet,Zendaya,Rebecca Ferguson", "Denis Villeneuve", 7.8, 12000),
    m(8, "Gravity", 2013, "Science Fiction|Thriller|Drama", "Two astronauts struggle to survive after debris destroys their shuttle in orbit.", "space,survival,orbit,disaster", "Sandra Bullock,George Clooney", "Alfonso Cuarón", 7.2, 11000),
    m(9, "Arrival", 2016, "Science Fiction|Drama|Mystery", "A linguist is recruited to communicate with mysterious alien visitors before war breaks out.", "aliens,language,first contact,time", "Amy Adams,Jeremy Renner,Forest Whitaker", "Denis Villeneuve", 7.6, 14000),
    m(10, "Ex Machina", 2015, "Science Fiction|Drama|Thriller", "A programmer is asked to test whether a reclusive founder's humanoid robot is truly conscious.", "artificial intelligence,robot,turing test,isolation", "Alicia Vikander,Domhnall Gleeson,Oscar Isaac", "Alex Garland", 7.6, 10000),
    m(11, "John Wick", 2014, "Action|Thriller|Crime", "A retired hitman returns to the underworld to avenge a wrong done to him.", "assassin,revenge,underworld,gunfight", "Keanu Reeves,Michael Nyqvist,Willem Dafoe", "Chad Stahelski", 7.2, 12000),
    m(12, "Die Hard", 1988, "Action|Thriller", "An off-duty cop battles terrorists who seize a skyscraper during a holiday party.", "skyscraper,hostage,terrorist,christmas", "Bruce Willis,Alan Rickman", "John McTiernan", 7.8, 9000),
    m(13, "Gladiator", 2000, "Action|Drama|Adventure", "A betrayed Roman general becomes a gladiator and seeks revenge on the corrupt emperor.", "rome,arena,revenge,empire", "Russell Crowe,Joaquin Phoenix", "Ridley Scott", 8.0, 14000),
    m(14, "The Avengers", 2012, "Action|Adventure|Science Fiction", "Earth's mightiest heroes must unite to stop an alien invasion led by a vengeful god.", "superhero,team,alien invasion,marvel", "Robert Downey Jr.,Chris Evans,Scarlett Johansson", "Joss Whedon", 7.4, 24000),
    m(15, "Spider-Man: Into the Spider-Verse", 2018, "Animation|Action|Adventure|Family", "A teenager becomes Spider-Man and meets heroes from other dimensions.", "superhero,multiverse,teenager,comic book", "Shameik Moore,Hailee Steinfeld", "Bob Persichetti", 8.4, 9000),
    m(16, "Toy Story", 1995, "Animation|Family|Comedy", "A cowboy doll feels threatened when a new space ranger toy becomes his owner's favourite.", "toys,friendship,rivalry,childhood", "Tom Hanks,Tim Allen", "John Lasseter", 7.9, 14000),
    m(17, "Finding Nemo", 2003, "Animation|Family|Adventure", "A timid clownfish crosses the ocean to rescue his son from a dentist's aquarium.", "ocean,fish,father son,journey", "Albert Brooks,Ellen DeGeneres", "Andrew Stanton", 7.8, 13000),
    m(18, "Up", 2009, "Animation|Family|Adventure|Comedy", "An elderly widower ties balloons to his house and flies to South America with an unexpected stowaway.", "balloons,old age,adventure,friendship", "Ed Asner,Jordan Nagai", "Pete Docter", 7.9, 14000),
    m(19, "Spirited Away", 2001, "Animation|Fantasy|Family", "A girl wanders into a world of spirits and must work in a bathhouse to free her parents.", "spirits,magic,bathhouse,coming of age", "Rumi Hiiragi,Miyu Irino", "Hayao Miyazaki", 8.5, 12000),
    m(20, "Coco", 2017, "Animation|Family|Fantasy|Music", "A boy who dreams of being a musician journeys through the Land of the Dead.", "music,family,day of the dead,afterlife", "Anthony Gonzalez,Gael García Bernal", "Lee Unkrich", 8.2, 9000),
    m(21, "The Lord of the Rings: The Fellowship of the Ring", 2001, "Adventure|Fantasy|Action", "A hobbit sets out with a company of allies to destroy a ring of terrible power.", "ring,quest,wizard,middle earth", "Elijah Wood,Ian McKellen,Viggo Mortensen", "Peter Jackson", 8.4, 20000),
    m(22, "Harry Potter and the Sorcerer's Stone", 2001, "Adventure|Fantasy|Family", "An orphan learns he is a wizard and begins his first year at a school of magic.", "wizard,magic school,orphan,friendship", "Daniel Radcliffe,Emma Watson,Rupert Grint", "Chris Columbus", 7.7, 19000),
    m(23, "Pan's Labyrinth", 2006, "Fantasy|Drama|War", "In fascist Spain a young girl escapes into a dark fairy-tale underworld.", "fairy tale,civil war,fantasy,faun", "Ivana Baquero,Sergi López", "Guillermo del Toro", 7.6, 8000),
    m(24, "The Shining", 1980, "Horror|Thriller", "A writer takes a winter caretaker job at an isolated hotel and slowly loses his mind.", "haunted hotel,isolation,madness,ghost", "Jack Nicholson,Shelley Duvall", "Stanley Kubrick", 8.2, 11000),
    m(25, "Get Out", 2017, "Horror|Mystery|Thriller", "A young man visits his girlfriend's family estate and uncovers a disturbing secret.", "social horror,hypnosis,secret,suburbia", "Daniel Kaluuya,Allison Williams", "Jordan Peele", 7.6, 13000),
    m(26, "A Quiet Place", 2018, "Horror|Science Fiction|Thriller", "A family lives in silence to hide from creatures that hunt by sound.", "silence,monsters,survival,family", "Emily Blunt,John Krasinski", "John Krasinski", 7.4, 9000),
    m(27, "Hereditary", 2018, "Horror|Mystery|Drama", "After a family matriarch dies, strange and terrifying events unravel her relatives.", "grief,cult,occult,family secrets", "Toni Collette,Alex Wolff", "Ari Aster", 7.3, 7000),
    m(28, "The Conjuring", 2013, "Horror|Thriller|Mystery", "Paranormal investigators help a family terrorised by a dark presence in their farmhouse.", "haunting,demon,paranormal,true story", "Vera Farmiga,Patrick Wilson", "James Wan", 7.5, 8000),
    m(29, "Superbad", 2007, "Comedy", "Two high school friends try to buy alcohol for a party before graduation.", "teenagers,party,friendship,high school", "Jonah Hill,Michael Cera", "Greg Mottola", 7.2, 6000),
    m(30, "The Grand Budapest Hotel", 2014, "Comedy|Drama|Crime|Adventure", "A legendary concierge and his young lobby boy are caught up in the theft of a priceless painting.", "hotel,painting,caper,quirky", "Ralph Fiennes,Tony Revolori", "Wes Anderson", 8.0, 12000),
    m(31, "Bridesmaids", 2011, "Comedy|Romance", "A maid of honour's life unravels as she competes with a rival to plan her best friend's wedding.", "wedding,friendship,rivalry,female ensemble", "Kristen Wiig,Maya Rudolph", "Paul Feig", 6.8, 5000),
    m(32, "The Hangover", 2009, "Comedy", "Three friends wake up from a bachelor party in Las Vegas with no memory and a missing groom.", "bachelor party,las vegas,mystery,friends", "Bradley Cooper,Ed Helms,Zach Galifianakis", "Todd Phillips", 7.3, 11000),
    m(33, "Knives Out", 2019, "Comedy|Crime|Mystery", "A detective investigates the death of a wealthy crime novelist surrounded by his scheming family.", "whodunit,detective,family,inheritance", "Daniel Craig,Ana de Armas,Chris Evans", "Rian Johnson", 7.9, 11000),
    m(34, "Titanic", 1997, "Drama|Romance", "A young aristocrat and a poor artist fall in love aboard the doomed ocean liner.", "ship,disaster,love story,class", "Leonardo DiCaprio,Kate Winslet", "James Cameron", 7.9, 22000),
    m(35, "La La Land", 2016, "Comedy|Drama|Romance|Music", "An aspiring actress and a jazz pianist chase their dreams and fall in love in Los Angeles.", "jazz,musical,dreams,los angeles", "Ryan Gosling,Emma Stone", "Damien Chazelle", 7.9, 13000),
    m(36, "The Notebook", 2004, "Romance|Drama", "A poor young man and a wealthy young woman fall in love in the 1940s and are torn apart.", "love story,letters,class,memory", "Ryan Gosling,Rachel McAdams", "Nick Cassavetes", 7.9, 9000),
    m(37, "Pride & Prejudice", 2005, "Drama|Romance", "A spirited young woman and a proud gentleman misjudge each other in Regency England.", "regency,class,courtship,period", "Keira Knightley,Matthew Macfadyen", "Joe Wright", 7.7, 6000),
    m(38, "Whiplash", 2014, "Drama|Music", "A young drummer is pushed to the brink by an abusive conservatory instructor.", "jazz,drumming,obsession,mentor", "Miles Teller,J.K. Simmons", "Damien Chazelle", 8.3, 13000),
    m(39, "The Shawshank Redemption", 1994, "Drama|Crime", "A banker wrongly convicted of murder finds hope and friendship inside a brutal prison.", "prison,friendship,hope,escape", "Tim Robbins,Morgan Freeman", "Frank Darabont", 8.7, 25000),
    m(40, "The Godfather", 1972, "Drama|Crime", "The ageing patriarch of a crime dynasty hands control to his reluctant youngest son.", "mafia,family,power,loyalty", "Marlon Brando,Al Pacino", "Francis Ford Coppola", 8.7, 18000),
    m(41, "Pulp Fiction", 1994, "Thriller|Crime|Comedy", "The lives of two hitmen, a boxer and a gangster's wife intertwine in four tales of violence and redemption.", "hitman,nonlinear,crime,dark comedy", "John Travolta,Samuel L. Jackson,Uma Thurman", "Quentin Tarantino", 8.5, 24000),
    m(42, "Se7en", 1995, "Crime|Mystery|Thriller", "Two detectives hunt a serial killer who uses the seven deadly sins as his motives.", "serial killer,detective,sins,dark", "Brad Pitt,Morgan Freeman", "David Fincher", 8.3, 17000),
    m(43, "Gone Girl", 2014, "Mystery|Thriller|Drama", "A husband becomes the prime suspect when his wife vanishes on their anniversary.", "missing wife,media,marriage,twist", "Ben Affleck,Rosamund Pike", "David Fincher", 7.9, 14000),
    m(44, "Parasite", 2019, "Comedy|Thriller|Drama", "A poor family schemes its way into the lives of a wealthy household with unforeseen consequences.", "class,con,family,dark comedy", "Song Kang-ho,Choi Woo-shik", "Bong Joon-ho", 8.5, 15000),
    m(45, "Saving Private Ryan", 1998, "Drama|History|War|Action", "A squad of soldiers is sent behind enemy lines to bring home a paratrooper whose brothers have died.", "world war two,d-day,soldiers,rescue", "Tom Hanks,Matt Damon", "Steven Spielberg", 8.2, 13000),
    m(46, "Dunkirk", 2017, "Action|Drama|History|Thriller|War", "Allied soldiers are surrounded on the beaches of Dunkirk and wait for rescue.", "world war two,evacuation,sea,air", "Fionn Whitehead,Tom Hardy", "Christopher Nolan", 7.5, 10000),
    m(47, "The Good, the Bad and the Ugly", 1966, "Western|Adventure", "Three gunslingers race across the American Civil War frontier to find buried gold.", "gold,gunslinger,civil war,desert", "Clint Eastwood,Eli Wallach", "Sergio Leone", 8.5, 7000),
    m(48, "Django Unchained", 2012, "Drama|Western", "A freed slave teams up with a bounty hunter to rescue his wife from a brutal plantation owner.", "bounty hunter,revenge,slavery,frontier", "Jamie Foxx,Christoph Waltz", "Quentin Tarantino", 8.2, 20000),
    m(49, "Moneyball", 2011, "Drama", "A baseball general manager uses statistics to build a competitive team on a tiny budget.", "baseball,statistics,underdog,true story", "Brad Pitt,Jonah Hill", "Bennett Miller", 7.6, 6000),
    m(50, "Planet Earth II", 2016, "Documentary", "Stunning footage follows animals through mountains, jungles, islands and cities around the world.", "nature,wildlife,animals,cinematography", "David Attenborough", "Ed Charles", 9.0, 2000),
]
