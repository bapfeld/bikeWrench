# This script is based off of https://github.com/marcusvolz/strava

source("header.R")

data <- process_data("data/gpx")

p1 <- plot_facets(data)

pdf("output/map_multiples.pdf", width = 20, height = 20)
print(p1)
dev.off()

p3 <- plot_elevations(data)
pdf("output/elevations_multiple.pdf", width = 20, height = 20)
print(p3)
dev.off()
