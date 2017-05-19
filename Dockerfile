FROM astrodigital/modispds:base

WORKDIR /build

COPY ./ /build/

RUN \
    pip3 install .

ENTRYPOINT ["modis-pds"]
CMD []
