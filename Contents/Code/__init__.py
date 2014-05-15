import time
from grooveshark import Grooveshark

################################################################################
TITLE       = 'Grooveshark'
ART         = 'art-default.jpg'
ICON        = 'icon-default.png'
SEARCH_ICON = 'icon-search.png'
PREFS_ICON  = 'icon-prefs.png'
PREFIX      = '/music/grooveshark'
shark       = Grooveshark()

################################################################################
def Start():
    DirectoryObject.thumb  = R(ICON)
    ObjectContainer.art    = R(ART)
    ObjectContainer.title1 = TITLE
    VideoClipObject.art    = R(ART)
    VideoClipObject.thumb  = R(ICON)

################################################################################
@handler(PREFIX, TITLE, art=ART, thumb=ICON)
def Main():
    oc = ObjectContainer(title2=TITLE)
    shark.authenticateUser(Prefs['username'], Prefs['password'])

    if shark.isAuthenticated():
        oc.add(DirectoryObject(key=Callback(Collection), title='Collection'))
        oc.add(DirectoryObject(key=Callback(Favorites), title='Favorites'))
        oc.add(DirectoryObject(key=Callback(Playlists), title='Playlists'))

    oc.add(DirectoryObject(key=Callback(Genres), title='Genres'))

    #Turning off for now
    #oc.add(DirectoryObject(key=Callback(Broadcasts), title='Broadcasts'))

    oc.add(DirectoryObject(key=Callback(Popular), title='Popular'))
    oc.add(InputDirectoryObject(key=Callback(Search), title="Search", prompt="Search for", thumb=R(SEARCH_ICON)))
    oc.add(PrefsObject(title='Preferences', thumb=R(PREFS_ICON)))
    return oc

################################################################################
@route(PREFIX + '/collection', page=int)
def Collection(page=0):
    oc = ObjectContainer(title2='Collection')

    library = shark.userGetSongsInLibrary(page)
    for song in library['Songs']:
        oc.add(CreateTrackObject(song=song, fn=GetStreamURL))

    if library['hasMore'] == True:
        oc.add(NextPageObject(key=Callback(Collection, page=page+1)))

    return oc

################################################################################
@route(PREFIX + '/favorites')
def Favorites():
    oc = ObjectContainer(title2='Favorites')

    favorites = shark.getFavorites()
    for song in favorites:
        oc.add(CreateTrackObject(song=song, fn=GetStreamURL))

    return oc

################################################################################
@route(PREFIX + '/playlists')
def Playlists():
    oc = ObjectContainer(title2='Playlists')

    playlists = shark.userGetPlaylists()
    for playlist in playlists['Playlists']:
        do = DirectoryObject(key = Callback(PlaylistsSubMenu, title=playlist['Name'], id=playlist['PlaylistID']), title=playlist['Name'])
        if 'Picture' in playlist and playlist['Picture'] != None:
            do.thumb = shark.playlist_base_url + '200_' + playlist['Picture']
        else:
            do.thumb = shark.no_album_url

        oc.add(do)

    return oc

################################################################################
@route(PREFIX + '/genres')
def Genres():
    oc = ObjectContainer(title2='Genres')

    tags = shark.getTopLevelTags()
    for tag in tags:
        oc.add(DirectoryObject(key = Callback(GenreSubMenu, title=tag['Tag'], id=tag['TagID']), title=tag['Tag']))

    return oc

################################################################################
@route(PREFIX + '/broadcasts')
def Broadcasts():
    oc = ObjectContainer(title2='Broadcasts')

    broadcasts = shark.getTopBroadcastsCombinedEx()
    for key, value in broadcasts['all'].iteritems():
        if 'n' in value and 's' in value:
            if 'active' in value['s']:
                if 'b' in value['s']['active']:
                    if 'tk' in value['s']['active']['b'] and value['s']['active']['b']['tk']:
                        song = {'SongID': value['s']['active']['b']['tk'],
                                'Name': value['n'],
                                'CoverArtFilename': shark.no_user_url}
                        if 'i' in value and value['i'] != None:
                            song['CoverArtFilename'] = shark.broadcast_base_url + value['i']
                        elif 'users' in value and len(value['users']) > 0 and 'Picture' in value['users'][0] and value['users'][0]['Picture'] != None:
                            song['CoverArtFilename'] = shark.users_base_url + value['users'][0]['Picture']

                        oc.add(CreateTrackObject(song=song, fn=GetBroadcastURL))

    return oc

################################################################################
@route(PREFIX + '/popular')
def Popular():
    oc = ObjectContainer(title2='Popular')
    oc.add(DirectoryObject(key = Callback(PopularSubMenu, title='Popular Today', type='daily'), title='Popular Today'))
    oc.add(DirectoryObject(key = Callback(PopularSubMenu, title='Popular Today', type='weekly'), title='Popular This Week'))
    oc.add(DirectoryObject(key = Callback(PopularSubMenu, title='Popular Today', type='monthly'), title='Popular This Month'))
    return oc

################################################################################
@route(PREFIX + '/playlistssubmenu')
def PlaylistsSubMenu(title, id):
    oc = ObjectContainer(title2=title)

    songs = shark.playlistGetSongs(id)
    for song in songs['Songs']:
            oc.add(CreateTrackObject(song=song, fn=GetStreamURL))

    return oc

################################################################################
@route(PREFIX + '/genresubmenu')
def GenreSubMenu(title, id):
    oc = ObjectContainer(title2=title)
    oc.add(DirectoryObject(key = Callback(GenrePlayMenu, title=title, id=id), title='Play ' + title))
    oc.add(DirectoryObject(key = Callback(GenrePlayMenu, title='Related Genres: ' + title, id=id, type='related'), title='Related Genres'))
    return oc

################################################################################
@route(PREFIX + '/genreplaymenu')
def GenrePlayMenu(title, id, type=None):
    oc = ObjectContainer(title2=title)
    info = shark.getPageInfoByIDType(id)

    if type == 'related':
        for song in info['Data']['RelatedTags']:
            oc.add(DirectoryObject(key = Callback(GenrePlayMenu, title=song['TagName'], id=song['TagID']), title='Play ' + song['TagName']))

    else:
        for song in info['Data']['Songs']:
            oc.add(CreateTrackObject(song=song, fn=GetStreamURL))

    return oc

################################################################################
@route(PREFIX + '/popularsubmenu')
def PopularSubMenu(title, type):
    oc = ObjectContainer(title2=title)

    songs = shark.popularGetSongs(type)
    for song in songs['Songs']:
        oc.add(CreateTrackObject(song=song, fn=GetStreamURL))

    return oc

################################################################################
@route(PREFIX + '/search')
def Search(query):
    oc = ObjectContainer(title2="Search Results")

    results = shark.getAutocompleteEx(query)
    
    if len(results) == 0:
        oc.header = 'Search Results'
        oc.message = 'No results found'        
    else:    
        for key, values in results.iteritems():        
            if key == 'artist':                
                for artist in values:
                    artistObj = ArtistObject(
                        key=Callback(ShowArtistOptions, name=artist['Name'], id=artist['ArtistID']),
                        rating_key=artist['ArtistID'],
                        title=artist['Name']
                    )
                    
                    if 'CoverArtFilename' in artist and artist['CoverArtFilename'] != None and "".join(artist['CoverArtFilename'].split()) != '':                    
                        artistObj.thumb=shark.artist_base_url + artist['CoverArtFilename']
                    else:
                        artistObj.thumb=shark.no_artist_url
                    
                    oc.add(artistObj)
            
            elif key == 'song':
                for song in values:
                    oc.add(CreateTrackObject(song=song, fn=GetStreamURL))
            
            elif key == 'album':
                for album in values:
                    albumObj = AlbumObject(
                        key=Callback(ShowAlbumOptions, name=album['AlbumName'], id=album['AlbumID']),
                        rating_key=album['AlbumID'],
                        artist=album['ArtistName'],
                        title=album['AlbumName']
                    )
                    
                    if 'CoverArtFilename' in album and album['CoverArtFilename'] != None and "".join(album['CoverArtFilename'].split()) != '':                    
                        albumObj.thumb=shark.album_base_url + album['CoverArtFilename']
                    else:
                        albumObj.thumb=shark.no_album_url
                    
                    oc.add(albumObj)    
    return oc

################################################################################
@route(PREFIX + '/showartistoptions')    
def ShowArtistOptions(name, id):
    oc = ObjectContainer(title2=name)
    
    albums = shark.artistGetAllAlbums(id)
    for album in albums['albums']:
        albumObj = AlbumObject(
            key=Callback(ShowAlbumOptions, name=album['Name'], id=album['AlbumID']),
            rating_key=album['AlbumID'],
            artist=name,
            title=album['Name']
        )
        
        if 'CoverArtFilename' in album and album['CoverArtFilename'] != None and "".join(album['CoverArtFilename'].split()) != '':                    
            albumObj.thumb=shark.album_base_url + album['CoverArtFilename']
        else:
            albumObj.thumb=shark.no_album_url
        
        oc.add(albumObj)
    
    return oc
    
################################################################################
@route(PREFIX + '/showalbumoptions')    
def ShowAlbumOptions(name, id):
    oc = ObjectContainer(title2=name)
    
    songs = shark.albumGetAllSongs(id)
    for song in songs:
        oc.add(CreateTrackObject(song=song, fn=GetStreamURL))
    
    return oc    

################################################################################
@route(PREFIX + '/createtrackobject', song=dict)
def CreateTrackObject(song, fn, include_container=False):    
    track_obj = TrackObject(
        key = Callback(CreateTrackObject, song=song, fn=fn, include_container=True),
        rating_key = song['SongID'],
        title = song['Name'],        
        items = [
            MediaObject(
                audio_codec = AudioCodec.MP3,
                container = 'mp3',
                parts = [
                    PartObject(key = Callback(fn, id=song['SongID'], ext='mp3'))
                ]
            )
        ]
    )
    
    if 'ArtistName' in song and song['ArtistName'] != None:
        track_obj.artist = song['ArtistName']
    
    if 'AlbumName' in song and song['AlbumName'] != None:
        track_obj.album = song['AlbumName']

    if 'TrackNum' in song and song['TrackNum'] != None:
        track_obj.index = int(song['TrackNum'])    

    if 'EstimateDuration' in song and song['EstimateDuration'] != None:
        track_obj.duration = int(song['EstimateDuration']) * 1000
    
    if 'CoverArtFilename' in song and song['CoverArtFilename'] != None and "".join(song['CoverArtFilename'].split()) != '':
        if song['CoverArtFilename'].startswith('http'):
            track_obj.thumb = song['CoverArtFilename']
        else:
            track_obj.thumb = shark.album_base_url + song['CoverArtFilename']
    else:        
        track_obj.thumb = shark.no_album_url

    if include_container:
        return ObjectContainer(objects=[track_obj])
    else:
        return track_obj

################################################################################
@route(PREFIX + '/getstreamurl')
def GetStreamURL(id):
    url, server, key = shark.getStreamKeyFromSongIDEx(id)
    Thread.Create(MarkDownloads, id=id, server=server, key=key)
    return Redirect(url)

################################################################################
@route(PREFIX + '/getbroadcasturl')
def GetBroadcastURL(id):
    url, server, key = shark.getStreamKeyFromFileToken(id)
    Thread.Create(MarkDownloads, id=id, server=server, key=key)
    return Redirect(url)

########################## Thread Function ####################################
def MarkDownloads(id, server, key):
    shark.markSongDownloadedEx(id, server, key)
    time.sleep(30)
    shark.markStreamKeyOver30Seconds(id, server, key)
    time.sleep(30)
    shark.markSongComplete(id, server, key)
    return