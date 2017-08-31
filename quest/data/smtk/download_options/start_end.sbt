<?xml version="1.0"?>
<SMTK_AttributeSystem Version="3">
  <!--**********  Category and Analysis Information ***********-->
  <!--**********  Attribute Definitions ***********-->
  <Definitions>
    <AttDef Type="TimeSeriesOptions" BaseType="" Version="0" Unique="true">
      <ItemDefinitions>
        <String Name="parameter" Label="Parameters to Download">
          <DiscreteInfo DefaultIndex="0">
          {% for name, value in parameters %}
            <Value Enum="{{name}}">{{value}}</Value>
          {% endfor %}
          </DiscreteInfo>
        </String>
        <DateTime
          Name="start"
          Label="Start Date"
          DisplayFormat="yyyy-MM-dd"
          ShowTimeZone="false"
          Optional="true"
          IsEnabledByDefault="true">
        </DateTime>
        <DateTime
          Name="end"
          Label="End Date"
          DisplayFormat="yyyy-MM-dd"
          ShowTimeZone="false"
          Optional="true"
          IsEnabledByDefault="true">
        </DateTime>
      </ItemDefinitions>
    </AttDef>
  </Definitions>
  <!--********** Workflow Views ***********-->
  <Views>
    <View
      TopLevel="true"
      Type="Instanced"
      Title="Options"
      FilterByAdvanceLevel="false"
      FilterByCategory="false">
      <InstancedAttributes>
        <Att Name="Options" Type="TimeSeriesOptions" />
      </InstancedAttributes>
    </View>
  </Views>
</SMTK_AttributeSystem>
