<template>
  <q-page>
    <q-splitter v-model="tab">

      <template v-slot:before>
        <q-tabs
          v-model="tab"
          vertical
          class="text-teal"
        >
          <q-tab name="records" icon="mail" label="Records" />
          <q-tab name="details" icon="alarm" label="Details" />
          <q-tab name="goaccess" icon="alarm" label="GoAccess" />
        </q-tabs>
      </template>

      <template v-slot:after>
        <q-tab-panels
          v-model="tab"
          animated
          swipeable
          vertical
          transition-prev="jump-up"
          transition-next="jump-up"
        >
        <q-tab-panel name="records">
          <div class="text-h4 q-mb-md">Records</div>
            <div class="row">
              <div class="col-12">
                <q-table
                  title="Access"
                  :data="data"
                  :columns="columns"
                  row-key="id"
                  virtual-scroll
                  :pagination.sync="pagination"
                  binary-state-sort
                  :filter="filter"
                  @request="onRequest"
                  :rows-per-page-options="[10, 20, 30]"
                >
                <template v-slot:top>
                <img
                  style="height: 50px; width: 50px"
                  src="https://cdn.quasar.dev/logo/svg/quasar-logo.svg"
                />
                <q-space />
                <q-btn flat color="primary" label="Update" @click="update" />
                <q-btn flat color="primary" label="Refresh" @click="getData" />
                </template>
                <template v-slot:body="props">
                  <q-tr :props="props">
                    <q-td v-for="col in columns" :key="col.field" :props="props">
                      <p v-if="col.field === 'byte'">
                        {{ props.row[col.field] | prettyBytes }}
                      </p>
                      <p v-else-if="col.field === 'date'">
                        {{ formatDate(props.row[col.field]) }}
                      </p>
                      <p v-else>{{ props.row[col.field] }}</p>
                    </q-td>
                  </q-tr>
                </template>
              </q-table>
            </div>
          </div>
        </q-tab-panel>

        <q-tab-panel name="details">
          <div class="text-h4 q-mb-md">Details</div>
            <div class="row">
              <q-toggle v-model="details.with_date" label="With date" @input="getDetail()"/>
              <q-space />
              <q-toggle v-model="details.with_refer" label="With refer" @input="getDetail()"/>
              <q-space />
              <q-select
                @input="val => { details.group_by = val ; getDetail()}"
                v-model="details.group_by"
                :options="details.groups"
                style="min-width: 150px"
              />
            </div>
            <div class="row">
              <div class="col-12">
                <q-table
                  title="Details"
                  :data="details.data"
                  :columns="details.columns"
                  row-key="id"
                  virtual-scroll
                  :pagination.sync="details.pagination"
                  binary-state-sort
                  @request="onRequestDetails"
                  :rows-per-page-options="[10, 20, 30]"
                >
                <template v-slot:body="props">
                  <q-tr :props="props">
                    <q-td v-for="col in details.columns" :key="col.field" :props="props">
                      <p v-if="col.field === 'bytes'">
                        {{ props.row[col.field] | prettyBytes }}
                      </p>
                      <p v-else-if="col.field === 'date'">
                        {{ formatDate(props.row[col.field]) }}
                      </p>
                      <p v-else>{{ props.row[col.field] }}</p>
                    </q-td>
                  </q-tr>
                </template>
                </q-table>
              </div>
            </div>
          </q-tab-panel>

        <q-tab-panel name="goaccess">
          <div class="row">
            <div class="col">
              <vue-aspect-ratio ar="2:1" width="100%">
                <iframe :src="urls.goaccess" style="width: 100%;height:100%" />
              </vue-aspect-ratio>
            </div>
          </div>
        </q-tab-panel>
        </q-tab-panels>
      </template>

    </q-splitter>

    <q-dialog v-model="dialog" :position="position">
      <q-card style="width: 350px">
        <q-card-section class="row items-center no-wrap">
          <div>
            <div class="text-weight-bold">Error</div>
            <div class="text-grey">{{ error }}</div>
          </div>
        </q-card-section>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script>
import format from 'date-format'

export default {
  name: 'PageIndex',
  data () {
    const base = ''
    return {
      tab: 'records',
      urls: {
        thead: base + '/fileds',
        data: base + '/query',
        details: base + '/bytes',
        goaccess: base + '/goaccess',
        update: base + '/update'
      },
      data: [],
      columns: [],
      pagination: {
        sortBy: 'ip',
        descending: false,
        page: 1,
        rowsPerPage: 10,
        rowsNumber: 10
      },
      loading: false,
      filter: '',
      error: '',
      position: 'top',
      dialog: false,
      details: {
        data: [],
        columns: [],
        loading: false,
        group_by: 'ip',
        groups: [],
        with_date: true,
        with_refer: true,
        pagination: {
          sortBy: 'bytes',
          descending: false,
          page: 1,
          rowsPerPage: 10,
          rowsNumber: 10
        }
      },
      goaccess: ''
    }
  },
  methods: {
    getThead () {
      const self = this
      this.$axios.get(this.urls.thead).then(response => {
        for (const i of response.data) {
          self.columns.push({
            name: i, align: 'center', label: i, field: i, sortable: true
          })
        }
      })

      this.$axios.get(this.urls.thead, {
        params: {
          group_by: true
        }
      }).then(response => {
        self.details.groups = response.data
      })
    },
    getData () {
      this.loading = true
      const self = this
      this.$axios.get(this.urls.data, {
        params: {
          start: this.pagination.page,
          length: this.pagination.rowsPerPage,
          sort_by: this.pagination.sortBy,
          desc: this.pagination.descending
        }
      }).then(response => {
        const data = response.data
        self.pagination.page = data.start
        self.pagination.rowsPerPage = data.length
        self.pagination.rowsNumber = data.total
        self.data = data.data
      }).catch(error => {
        self.error = error.data
        self.dialog = true
      }).finally(() => {
        self.loading = false
      })
    },
    onRequest (props) {
      const { page, rowsPerPage, sortBy, descending } = props.pagination
      // emulate server
      this.pagination.page = page
      this.pagination.rowsPerPage = rowsPerPage
      this.pagination.sortBy = sortBy
      this.pagination.descending = descending

      // ...and turn of loading indicator
      this.getData()
    },

    getDetail () {
      this.details.loading = true
      const self = this
      this.$axios.get(this.urls.details, {
        params: {
          start: this.details.pagination.page,
          length: this.details.pagination.rowsPerPage,
          sort_by: this.details.pagination.sortBy,
          desc: this.details.pagination.descending,
          by: this.details.group_by,
          with_date: this.details.with_date,
          with_refer: this.details.with_refer
        }
      }).then(response => {
        const data = response.data
        self.details.pagination.page = data.start
        self.details.pagination.rowsPerPage = data.length
        self.details.pagination.rowsNumber = data.total
        self.details.data = data.data

        const columns = []
        for (const i of response.data.header) {
          columns.push({
            name: i, align: 'center', label: i, field: i, sortable: true
          })
        }
        self.details.columns = columns
      }).catch(error => {
        self.error = error.data
        self.dialog = true
      }).finally(() => {
        self.details.loading = false
      })
    },

    onRequestDetails (props) {
      const { page, rowsPerPage, sortBy, descending } = props.pagination

      // emulate server
      this.details.pagination.page = page
      this.details.pagination.rowsPerPage = rowsPerPage
      this.details.pagination.sortBy = sortBy
      this.details.pagination.descending = descending

      // ...and turn of loading indicator
      this.getDetail()
    },

    formatDate (str) {
      return format.asString('yyyy-MM-dd', format.parse('yyyy-MM-dd', str))
    },

    update () {
      this.$axios.get(this.urls.update)
    }
  },
  mounted () {
    this.getThead()
    this.getData()
    this.getDetail()
  }
}
</script>
