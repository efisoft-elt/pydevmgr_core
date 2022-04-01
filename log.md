# 0.4.3 
- Add GenConf typing to allow loading string as content of a config file 
- io.load_config can now handle  '/file/path.yml[a.b.c]'
- Add conparser  to build parser in pydantic model 

# 0.4.2
- The default fget and fset of NodeAlias1 is returning the value, as it should be !

# 0.4.1
- added the path function 
- NodeAlias and DataLink are now using the path function natively  
- add the handling of flag 'cfgfile' and 'cfgfile_path' for all Base configuration. 
    A file can be now loaded on the fly inside a configuration payload 
    e.g.
        type: Motor
        cfgfile: tins/motor.yml
        cfgfile_pat: motor 
    Will load the given cfgfile and extract the motor1 configuration

# 0.4.0

The 0.4 version is I think the one forward to a stable version. Feedback are needed. 
Many under the whode changes since v0.3. v0.3 ideas has been droped. 
