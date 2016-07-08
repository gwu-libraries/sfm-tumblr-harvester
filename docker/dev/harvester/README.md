# sfm-tumblr-harvester dev docker container

A docker container for running sfm-tumblr-harvester as a service.
The harvester code must be mounted as `/opt/sfm-tumblr-harvester`, the sfm-utils code as `/opt/sfm-utils` and the warcprox code as `/opt/warcprox`.
For example:

```python
volumes:
    - "/my_directory/sfm-tumblr-harvester:/opt/sfm-tumblr-harvester"
    - "/my_directory/sfm-utils:/opt/sfm-utils"
    - "/my_directory/warcprox:/opt/warcprox"
```

This container requires a link to a container running the queue. This must be linked with the alias `mq`.  
For example:

```python
links:
    - sfmrabbit:mq
```
