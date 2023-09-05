import os
import pandas as pd
import geopandas as gpd
import folium as f
from branca import element

# reading csv file into pandas, removing extra columns
file = os.path.basename('Downloads\VS20_Indicators.csv')
df = pd.read_csv(file)
cols = df.columns.values[3:]
# new empty dataframe
bcs = pd.DataFrame({"indicator" : [], "CSA2020" : [] ,"Year" : [] ,"category" : []}, index = [])

# loops through indicators to populate dataframe
for i in range(len(cols)):
    # find maximum year of available data (most recent year with data) for each indicator
    maxyear = df.loc[(df[cols[i]].isna() == False)]['Year'].max()
    if maxyear == maxyear:
        # create a subset of original dataframe with most recent year
        year = df[df['Year']==maxyear]
        try:
            # find which CSA has the highest value for each indicator
            x = year.loc[year[cols[i]].idxmax()]
            s = year[cols[i]].transform(lambda x: x==x.max())
            if sum(bool(a) for a in s) <= 1:
                maxcsa = x[2]
                # output to new dataframe
                bcs.loc[len(bcs.index)] = [cols[i], maxcsa, maxyear, 'Highest'] 
            # if there are multiple CSAs tied for the highest value, look at the next most recent year of data
            else:
                while sum(bool(a) for a in s) > 1:
                    # keeps looping until a year is found where there are no ties in highest value
                    maxyear = maxyear-1
                    year = df[df['Year']==maxyear]
                    x = year.loc[year[cols[i]].idxmax()]
                    s = year[cols[i]].transform(lambda x: x==x.max())
                    maxcsa = x[2]
                # output to new dataframe
                bcs.loc[len(bcs.index)] = [cols[i], maxcsa, maxyear, 'Highest']
        # in cases when all years have ties, this statement will stop the loop
        except:
            pass
        # resets the process for minimum value of each indicator by reseting to most recent year of data
        maxyear = df.loc[(df[cols[i]].isna() == False)]['Year'].max()
        # create a subset of original dataframe with most recent year
        year = df[df['Year']==maxyear]
        try:
            # find which CSA has the lowest value for each indicator
            xx = year.loc[year[cols[i]].idxmin()]
            s = year[cols[i]].transform(lambda xx: xx==xx.min())
            if sum(bool(a) for a in s) <= 1:
                mincsa = xx[2]
                # output to new dataframe
                bcs.loc[len(bcs.index)] = [cols[i], mincsa, maxyear, 'Lowest']
            # if there are multiple CSAs tied for the lowest value, look at the next most recent year of data
            else:
                while sum(bool(a) for a in s) > 1:
                    # keeps looping until a year is found where there are no ties in lowest value
                    maxyear = maxyear-1
                    year = df[df['Year']==maxyear]
                    xx = year.loc[year[cols[i]].idxmin()]
                    s = year[cols[i]].transform(lambda xx: xx==xx.min())
                    mincsa = xx[2]
                # output to new dataframe
                bcs.loc[len(bcs.index)] = [cols[i], mincsa, maxyear, 'Lowest']
        # in cases when all years have ties, this statement will stop the loop
        except:
            pass

# restructure dataframe so that each superlative is grouped by CSA 
bcs['Year'] = bcs['Year'].astype(int)
bcs['popup'] = bcs['category'] + " " + bcs['indicator'] + " (" + bcs['Year'].astype(str) + ")"
bcs = bcs.groupby('CSA2020')['popup'].apply(list)

# correcting CSA names to match geojson
bcs['Orchard Ridge/Armistead']=bcs['Claremont/Armistead']
bcs['Oliver/Johnston Square']=bcs['Greenmount East']
bcs['Hampden/Remington']=bcs['Medfield/Hampden/Woodberry/Remington']
bcs['Midtown/Bolton Hill']=bcs['Midtown']
bcs['Oldtown/Eager Park']=bcs['Oldtown/Middle East']
bcs['Greektown/Bayview']=bcs['Orangeville/East Highlandtown']
bcs['Poppleton/Hollins Market']=bcs['Poppleton/The Terraces/Hollins Market']
bcs['Carrollton Ridge/Franklin Square']=bcs['Southwest Baltimore']
bcs['Pigtown/Carroll Park']=bcs['Washington Village/Pigtown']

# converting to dictionary where each CSA is a key and a list of superlatives are the value
bcs = bcs.to_dict()
for keys, values in bcs.items():
    concat = ''
    for i in values:
        # concatenating superlatives and delimiting breaks between records with '?'
        concat = concat + ' ' + i + ',?'
    # removing final delimiter from values
    bcs[keys] = concat[:-2]

# manually adding pop-up text for CSAs with no superlatives
bcs['Beechfield/Ten Hills/West Hills']='None, but previously had the Lowest Percent of Businesses that are 2 Years old or Less in 2015. The community that currently holds that distinction is Westport/Mount Winans/Lakeland'
bcs['Chinquapin Park/Belvedere']='None, but previously had the Highest Percent of Commercial Properties with Rehab Permits Above $5,000 in 2014. The community that currently holds that distinction is Cross-Country/Cheswolde'
bcs['Greater Govans']='None, but previously had the Lowest Total Dollar Amount Invested in Small Businesses per 50 Businesses in 2019. The community that currently holds that distinction is Dickeyville/Franklintown'
bcs['Hamilton Hills']='None, but previously had the Lowest Percent of Population that Walks to Work in 2016. The community that currently holds that distinction is Edmondson Village'
bcs['Greater Lauraville']='None, but previously had the Highest Percent of Households Earning $60,000 to $75,000 in 2016. The community that currently holds that distinction is Downtown/Seton Hill'

# converting dictionary back to dataframe
bcs = pd.DataFrame({'CSA2020' : bcs.keys(),'popup': bcs.values()})

### Optional output to CSV:
### bcs.to_csv('bcs_output',index=False)

# reading the geojson and cleaning the data
url = 'https://services1.arcgis.com/mVFRs7NF4iFitgbY/arcgis/rest/services/Community_Statistical_Areas_2020/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson'
geojson = gpd.read_file(url)
geojson.loc[geojson.CSA2020=='Oliver/Johnson Square','CSA2020'] = 'Oliver/Johnston Square'

# joining the dataframe to the geojson
geojson = geojson.merge(bcs, on='CSA2020')

# setting up folium map
mymap = f.Map(location=[39.299236, -76.609383], zoom_start=12,tiles=None)
f.TileLayer('CartoDB positron',name="Light Map",control=False).add_to(mymap)

# polygon style and highlight style
style_function = lambda x: {'fillColor': '#ffffff', 
                            'color':'#000000', 
                            'fillOpacity': 0.2, 
                            'weight': 3}

highlight_function = lambda x: {'fillColor': '#0055ff', 
                                'color':'#000000', 
                                'fillOpacity': 0.1,
                                'weight': 5}

# displaying geojson joined data onto the folium map
for i in range(0,len(geojson)):
    # formatting the pop-up, replacing delimiters with line breaks
    html = f"<b><h4>{geojson['CSA2020'][i]}:</h4></b>{geojson.popup.str.replace('?','<br>',regex=True)[i]}."
    # customizing pop-up height to be dynamic based on the amount of content being displayed
    if len(geojson['popup'][i]) < 300:
        height = 75+(len(geojson['popup'][i]))/2
    else:
        height = 225
    # using iframe to support html pop-up
    iframe = element.IFrame(html=html, width=400,height=height)
    # writing each feature from the geojson
    csadata = f.features.GeoJson(
        gpd.GeoDataFrame(geojson.iloc[[i]]),
        control=False,
        style_function=style_function,
        highlight_function=highlight_function,
        popup=f.map.Popup(html=iframe,parse_html=True, max_width=400),
        # adding tooltip with CSA name while hovering
        tooltip=f.features.GeoJsonTooltip(fields=['CSA2020'],labels=False)
    )
    # add to folium map
    csadata.add_to(mymap)

### save as HTML 
### mymap.save('BaltimoreCommunitySuperlatives.html')

mymap