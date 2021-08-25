const HQ_COORDS = [-25.727827, 31.868066]

// Icon size in pixels
const ICON_SIZE = 38

const iconOpts = url => {
    return {
        html: `<img src="${url}" onload="SVGInject(this)"></img>`,
        className: 'div-icon',
        iconSize: [ICON_SIZE, ICON_SIZE],
        iconAnchor: [ICON_SIZE / 2, ICON_SIZE - 1],
        popupAnchor: [0, -ICON_SIZE]
    }
}

function iconOptsWithId(iconOpts, id) {
    const iconOptsClone = {...iconOpts}
    const innerHtml = iconOptsClone.html
    const wrapper = $(`#req-${id}`)[0]
    if (wrapper){
        // if it exists
        const elemClone = wrapper.cloneNode(true)
        elemClone.innerHTML = innerHtml
        iconOptsClone.html = elemClone.outerHTML
    } else {
        iconOptsClone.html = `<div id="req-${id}">${innerHtml}</div>`
    }
    return iconOptsClone
}

const SELECTED_REQ_ICON_OPTS = Object.freeze(iconOpts('/static/lib/bootstrap-icons-1.5.0/geo-alt-fill.svg'))
const UNSELECTED_REQ_ICON_OPTS = Object.freeze(iconOpts('/static/lib/bootstrap-icons-1.5.0/geo-alt.svg'))

const HQ_MARKER_ICON = L.divIcon(iconOpts('/static/lib/bootstrap-icons-1.5.0/recycle.svg'))
const SELECTED_REQ_ICON = L.divIcon(SELECTED_REQ_ICON_OPTS)
const UNSELECTED_REQ_ICON = L.divIcon(UNSELECTED_REQ_ICON_OPTS)

const selectedReqIconWithId = id => L.divIcon(iconOptsWithId(SELECTED_REQ_ICON_OPTS, id))
const unselectedReqIconWithId = id => L.divIcon(iconOptsWithId(UNSELECTED_REQ_ICON_OPTS, id))

const map = L.map('map', {
    dragging: !L.Browser.mobile,
    gestureHandling: true,
    zoomSnap: 0.1
})

map.setView(HQ_COORDS, 14);

const HQ_MARKER = makeMarker(HQ_COORDS, HQ_MARKER_ICON, 'SiyaBuddy HQ')
map.addLayer(HQ_MARKER.layer)
HQ_MARKER.isDisplayed = true

L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    // attribution requirement from https://www.openstreetmap.org/copyright
    attribution: '&copy; Base map and data from <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> and OpenStreetMap Foundation'
}).addTo(map)

function makeMarker(loc, icon, reqId = undefined, msg = undefined) {
    const marker = L.marker(loc, { icon: icon })
    if (msg !== undefined) {
        marker.bindPopup(msg)
    }

    return { 'layer': marker, isSelected: false, isDisplayed: false, reqId: reqId }
}

function addMarkerToMap(marker) {
    if (!marker.isDisplayed) {
        map.addLayer(marker.layer)
        marker.isDisplayed = true
    }
}

function removeMarkerFromMap(marker) {
    if (marker.isDisplayed) {
        map.removeLayer(marker.layer)
        marker.isDisplayed = false
    }
}

function selectMarker(marker) {
    marker.layer.setIcon(selectedReqIconWithId(marker.reqId))
    marker.isSelected = true
}

function deSelectMarker(marker) {
    marker.layer.setIcon(unselectedReqIconWithId(marker.reqId))
    marker.isSelected = false
}

function fitMapToMarkersBounds(markers) {
    if (markers.length !== 0) {
        map.fitBounds(L.latLngBounds(markers.map(marker => marker.layer.getLatLng())),
                     { padding: [ICON_SIZE, ICON_SIZE]})
    }
}

function getSelectedMarkerIds() {
    return Object.entries(markerMap)
                 .filter(entry => entry[1].isSelected)
                 .map(entry => entry[0])
}

function getUnSelectedMarkerIds() {
    return Object.entries(markerMap)
                 .filter(entry => !entry[1].isSelected)
                 .map(entry => entry[0])
}

function getClickedLocation(ev, locationInput, manualInputMarker) {
    clearValidityIndicators(locationInput)

    manualInputMarker.layer.setLatLng(ev.latlng)
    addMarkerToMap(manualInputMarker)

    const prettyPrint = `${ev.latlng.lat} ${ev.latlng.lng}`
    locationInput.attr('placeholder', prettyPrint)

    return ev.latlng
}

const markerMap = {}

function registerPin(pin) {
    const marker = makeMarker(pin.loc, unselectedReqIconWithId(pin.reqId), pin.reqId, pin.msg)
    markerMap[pin.reqId] = marker
    addMarkerToMap(marker)
}

pins.forEach(registerPin)
fitMapToMarkersBounds(Object.values(markerMap))

