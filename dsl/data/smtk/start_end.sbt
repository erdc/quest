<?xml version="1.0"?>
<SMTK_AttributeSystem Version="2">
  <!--**********  Category and Analysis Information ***********-->
  <!--**********  Attribute Definitions ***********-->
  <Definitions>
    <AttDef Type="DownloadOptions" BaseType="" Version="0" Unique="true">
      <ItemDefinitions>
            <String Name="Parameters" Label="Parameters to Download">
              <DiscreteInfo DefaultIndex="0">
              {% for name, value in parameters %}
                <Value Enum="{{name}}">{{value}}</Value>
              {% endfor %}
              </DiscreteInfo>
            </String>
            <String Name="start" Label="Start Date" Optional="true" IsEnabledByDefault="true">
              <BriefDescription>Format yyyy-mm-dd</BriefDescription>
            </String>
            <String Name="end" Label="End Date" Optional="true" IsEnabledByDefault="true">
              <BriefDescription>Format yyyy-mm-dd</BriefDescription>
            </String>
      </ItemDefinitions>
    </AttDef>
  </Definitions>
  <!--********** Workflow Views ***********-->
  <Views>
    <View Type="Instanced" Title="Options">
      <InstancedAttributes>
        <Att Name="{{title}}" Type="DownloadOptions" />
      </InstancedAttributes>
    </View>
  </Views>
</SMTK_AttributeSystem>
